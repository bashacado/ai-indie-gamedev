#!/usr/bin/env python3
"""
cs_interface_mapper.py
Parses Unity C# scripts and produces lightweight .md interface maps.
Each output file captures the public API surface of a script so an AI
can know exactly how to interface with it without reading full source.

Usage:
   python cs_interface_mapper.py <input_dir> [output_dir]

If output_dir is omitted, defaults to <input_dir>/_interface_maps/
"""

import os
import sys
import re
import argparse
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


# ── Data Structures ──────────────────────────────────────────────────

@dataclass
class EnumInfo:
   name: str
   access: str
   values: list[str] = field(default_factory=list)

@dataclass
class FieldInfo:
   name: str
   type_name: str
   access: str
   is_static: bool = False
   is_readonly: bool = False
   is_serialized: bool = False
   default_value: Optional[str] = None

@dataclass
class PropertyInfo:
   name: str
   type_name: str
   access: str
   has_getter: bool = False
   has_setter: bool = False
   is_static: bool = False

@dataclass
class ParameterInfo:
   name: str
   type_name: str
   default_value: Optional[str] = None

@dataclass
class MethodInfo:
   name: str
   return_type: str
   access: str
   parameters: list[ParameterInfo] = field(default_factory=list)
   is_static: bool = False
   is_virtual: bool = False
   is_override: bool = False
   is_abstract: bool = False
   is_async: bool = False
   is_coroutine: bool = False

@dataclass
class ClassInfo:
   name: str
   access: str
   base_classes: list[str] = field(default_factory=list)
   is_abstract: bool = False
   is_static: bool = False
   is_partial: bool = False
   is_struct: bool = False
   is_interface: bool = False
   fields: list[FieldInfo] = field(default_factory=list)
   properties: list[PropertyInfo] = field(default_factory=list)
   methods: list[MethodInfo] = field(default_factory=list)
   enums: list[EnumInfo] = field(default_factory=list)
   nested_classes: list["ClassInfo"] = field(default_factory=list)

@dataclass
class FileInfo:
   filepath: str
   filename: str
   namespace: Optional[str] = None
   usings: list[str] = field(default_factory=list)
   classes: list[ClassInfo] = field(default_factory=list)
   top_level_enums: list[EnumInfo] = field(default_factory=list)
   project_dependencies: list[str] = field(default_factory=list)


# ── Regex Patterns ───────────────────────────────────────────────────

_RE_USING = re.compile(r'^\s*using\s+([\w.]+)\s*;', re.MULTILINE)
_RE_NAMESPACE = re.compile(r'^\s*namespace\s+([\w.]+)', re.MULTILINE)

_RE_CLASS = re.compile(
   r'(?P<access>public|private|protected|internal)?\s*'
   r'(?P<abstract>abstract\s+)?'
   r'(?P<static>static\s+)?'
   r'(?P<partial>partial\s+)?'
   r'(?P<kind>class|struct|interface)\s+'
   r'(?P<name>\w+)'
   r'(?:<[^>]+>)?'               # generic params
   r'(?:\s*:\s*(?P<bases>[^{]+?))?'
   r'\s*\{'
)

_RE_ENUM = re.compile(
   r'(?P<access>public|private|protected|internal)?\s*'
   r'enum\s+(?P<name>\w+)\s*(?::\s*\w+\s*)?\{'
)

_RE_FIELD = re.compile(
   r'^\s*'
   r'(?P<attrs>(?:\[[\w\s,()="\.]+\]\s*)*)'
   r'(?P<access>public|private|protected|internal)\s+'
   r'(?P<static>static\s+)?'
   r'(?P<readonly>readonly\s+)?'
   r'(?P<type>[\w<>\[\],\s\?\.]+?)\s+'
   r'(?P<name>\w+)\s*'
   r'(?:=\s*(?P<default>[^;]+))?\s*;',
   re.MULTILINE
)

_RE_PROPERTY = re.compile(
   r'^\s*'
   r'(?P<access>public|private|protected|internal)\s+'
   r'(?P<static>static\s+)?'
   r'(?P<type>[\w<>\[\],\s\?\.]+?)\s+'
   r'(?P<name>\w+)\s*\{',
   re.MULTILINE
)

_RE_METHOD = re.compile(
   r'^\s*'
   r'(?P<attrs>(?:\[[\w\s,()="\.]+\]\s*)*)'
   r'(?P<access>public|private|protected|internal)\s+'
   r'(?P<static>static\s+)?'
   r'(?P<virtual>virtual\s+)?'
   r'(?P<override>override\s+)?'
   r'(?P<abstract>abstract\s+)?'
   r'(?P<async>async\s+)?'
   r'(?P<return>[\w<>\[\],\s\?\.]+?)\s+'
   r'(?P<name>\w+)\s*'
   r'(?:<[^>]+>)?\s*'           # generic params
   r'\((?P<params>[^)]*)\)',
   re.MULTILINE
)

_RE_SERIALIZE_FIELD = re.compile(r'\[SerializeField\]')
_RE_HEADER = re.compile(r'\[Header\("([^"]+)"\)\]')
_RE_TOOLTIP = re.compile(r'\[Tooltip\("([^"]+)"\)\]')


# ── Helpers ──────────────────────────────────────────────────────────

def _strip_comments(src: str) -> str:
   """Remove single-line and multi-line comments."""
   src = re.sub(r'//.*?$', '', src, flags=re.MULTILINE)
   src = re.sub(r'/\*.*?\*/', '', src, flags=re.DOTALL)
   return src


def _extract_brace_block(src: str, start_pos: int) -> str:
   """Extract content between matching braces starting at start_pos."""
   depth = 0
   i = start_pos
   while i < len(src):
      if src[i] == '{':
         depth += 1
      elif src[i] == '}':
         depth -= 1
         if depth == 0:
            return src[start_pos:i + 1]
      i += 1
   return src[start_pos:]


def _parse_parameters(param_str: str) -> list[ParameterInfo]:
   """Parse a method parameter string into ParameterInfo list."""
   params = []
   param_str = param_str.strip()
   if not param_str:
      return params

   # Split respecting generics
   depth = 0
   current = ""
   for ch in param_str:
      if ch in '<(':
         depth += 1
      elif ch in '>)':
         depth -= 1
      elif ch == ',' and depth == 0:
         current = current.strip()
         if current:
            params.append(current)
         current = ""
         continue
      current += ch
   current = current.strip()
   if current:
      params.append(current)

   result = []
   for p in params:
      # Remove attributes
      p = re.sub(r'\[[\w\s,()="\.]+\]\s*', '', p).strip()
      # Remove param modifiers
      for mod in ('ref ', 'out ', 'in ', 'params ', 'this '):
         if p.startswith(mod):
            p = p[len(mod):]

      parts = p.rsplit('=', 1)
      default_val = parts[1].strip() if len(parts) > 1 else None
      type_and_name = parts[0].strip()

      # Split last token as name, rest as type
      tokens = type_and_name.rsplit(None, 1)
      if len(tokens) == 2:
         result.append(ParameterInfo(
            name=tokens[1],
            type_name=tokens[0].strip(),
            default_value=default_val
         ))
      elif len(tokens) == 1:
         result.append(ParameterInfo(
            name=tokens[0],
            type_name="?",
            default_value=default_val
         ))
   return result


def _is_unity_lifecycle(name: str) -> bool:
   """Check if method is a known Unity lifecycle callback."""
   unity_callbacks = {
      'Awake', 'Start', 'Update', 'FixedUpdate', 'LateUpdate',
      'OnEnable', 'OnDisable', 'OnDestroy', 'OnGUI',
      'OnTriggerEnter', 'OnTriggerExit', 'OnTriggerStay',
      'OnTriggerEnter2D', 'OnTriggerExit2D', 'OnTriggerStay2D',
      'OnCollisionEnter', 'OnCollisionExit', 'OnCollisionStay',
      'OnCollisionEnter2D', 'OnCollisionExit2D', 'OnCollisionStay2D',
      'OnMouseDown', 'OnMouseUp', 'OnMouseEnter', 'OnMouseExit',
      'OnMouseOver', 'OnMouseDrag',
      'OnBecameVisible', 'OnBecameInvisible',
      'OnApplicationPause', 'OnApplicationQuit', 'OnApplicationFocus',
      'OnDrawGizmos', 'OnDrawGizmosSelected',
      'OnValidate', 'Reset',
      'OnAnimatorMove', 'OnAnimatorIK',
      'OnRenderObject', 'OnWillRenderObject', 'OnPreRender', 'OnPostRender',
      'OnRenderImage',
   }
   return name in unity_callbacks


# ── Parser ───────────────────────────────────────────────────────────

def _parse_file(filepath: str) -> FileInfo:
   """Parse a single C# file and extract its interface surface."""
   with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
      raw_src = f.read()

   src = _strip_comments(raw_src)
   info = FileInfo(
      filepath=filepath,
      filename=os.path.basename(filepath),
   )

   # Usings
   info.usings = _RE_USING.findall(src)

   # Namespace
   ns_match = _RE_NAMESPACE.search(src)
   if ns_match:
      info.namespace = ns_match.group(1)

   # Top-level enums — only those NOT inside a class block
   # Find the position of first class/struct/interface opening brace
   first_class = _RE_CLASS.search(src)
   enum_boundary = first_class.start() if first_class else len(src)
   for m in _RE_ENUM.finditer(src):
      if m.start() >= enum_boundary:
         break
      access = m.group('access') or 'internal'
      name = m.group('name')
      brace_start = m.end() - 1
      block = _extract_brace_block(src, brace_start)
      inner = block[1:-1].strip()
      values = [v.strip().split('=')[0].strip()
                for v in inner.split(',') if v.strip()]
      info.top_level_enums.append(EnumInfo(
         name=name, access=access, values=values
      ))

   # Classes / structs / interfaces
   for m in _RE_CLASS.finditer(src):
      brace_pos = src.index('{', m.start())
      block = _extract_brace_block(src, brace_pos)
      inner = block[1:-1]

      bases_raw = m.group('bases')
      bases = []
      if bases_raw:
         # Parse base classes respecting generics
         depth = 0
         current = ""
         for ch in bases_raw:
            if ch == '<':
               depth += 1
            elif ch == '>':
               depth -= 1
            elif ch == ',' and depth == 0:
               current = current.strip()
               if current and current != 'where':
                  bases.append(current)
               current = ""
               continue
            current += ch
         current = current.strip()
         # Stop at 'where' constraints
         if current and not current.startswith('where'):
            bases.append(current.split(' where ')[0].strip())

      cls = ClassInfo(
         name=m.group('name'),
         access=m.group('access') or 'internal',
         base_classes=bases,
         is_abstract=bool(m.group('abstract')),
         is_static=bool(m.group('static')),
         is_partial=bool(m.group('partial')),
         is_struct=(m.group('kind') == 'struct'),
         is_interface=(m.group('kind') == 'interface'),
      )

      # Fields
      for fm in _RE_FIELD.finditer(inner):
         access = fm.group('access')
         attrs = fm.group('attrs') or ''
         is_serialized = bool(_RE_SERIALIZE_FIELD.search(attrs))

         # Only track public fields and [SerializeField] private fields
         if access != 'public' and not is_serialized:
            continue

         # Skip if this looks like it's inside a method body
         # (rough heuristic: check if preceded by { at same indent level)
         type_name = fm.group('type').strip()

         # Exclude common false positives
         if type_name in ('return', 'yield', 'var', 'throw', 'new'):
            continue

         cls.fields.append(FieldInfo(
            name=fm.group('name'),
            type_name=type_name,
            access=access,
            is_static=bool(fm.group('static')),
            is_readonly=bool(fm.group('readonly')),
            is_serialized=is_serialized,
            default_value=fm.group('default'),
         ))

      # Properties (public only)
      for pm in _RE_PROPERTY.finditer(inner):
         if pm.group('access') != 'public':
            continue
         prop_name = pm.group('name')
         # Skip if it collides with a method name (false positive)
         type_name = pm.group('type').strip()
         if type_name in ('return', 'yield', 'var', 'throw', 'new', 'class', 'enum', 'struct', 'interface', 'event'):
            continue
         # Skip if this matches an enum or nested class name
         known_type_names = {e.name for e in cls.enums}
         if prop_name in known_type_names:
            continue
         # Skip lines that are actually type declarations
         line_start = inner.rfind('\n', 0, pm.start()) + 1
         line_text = inner[line_start:pm.end()].strip()
         if re.match(r'(?:public|private|protected|internal)\s+(?:enum|class|struct|interface)\s+', line_text):
            continue

         brace_start_p = pm.end() - 1
         if brace_start_p < len(inner):
            prop_block = _extract_brace_block(inner, brace_start_p)
         else:
            prop_block = ""

         has_getter = 'get' in prop_block
         has_setter = 'set' in prop_block
         has_private_setter = bool(re.search(r'private\s+set', prop_block))
         has_private_getter = bool(re.search(r'private\s+get', prop_block))

         cls.properties.append(PropertyInfo(
            name=prop_name,
            type_name=type_name,
            access='public',
            has_getter=has_getter and not has_private_getter,
            has_setter=has_setter and not has_private_setter,
            is_static=bool(pm.group('static')),
         ))

      # Methods (public + protected virtual/override/abstract)
      for mm in _RE_METHOD.finditer(inner):
         access = mm.group('access')
         is_virtual = bool(mm.group('virtual'))
         is_override = bool(mm.group('override'))
         is_abstract = bool(mm.group('abstract'))
         name = mm.group('name')
         ret = mm.group('return').strip()

         # Skip non-public unless it's a protected virtual/override
         if access == 'private':
            continue
         if access == 'internal' and not (is_virtual or is_override or is_abstract):
            continue
         if access == 'protected' and not (is_virtual or is_override or is_abstract):
            continue

         # Detect coroutines
         is_coroutine = (ret == 'IEnumerator')

         cls.methods.append(MethodInfo(
            name=name,
            return_type=ret,
            access=access,
            parameters=_parse_parameters(mm.group('params')),
            is_static=bool(mm.group('static')),
            is_virtual=is_virtual,
            is_override=is_override,
            is_abstract=is_abstract,
            is_async=bool(mm.group('async')),
            is_coroutine=is_coroutine,
         ))

      # Nested enums
      for em in _RE_ENUM.finditer(inner):
         e_access = em.group('access') or 'internal'
         if e_access not in ('public', 'internal'):
            continue
         e_name = em.group('name')
         e_brace = em.end() - 1
         e_block = _extract_brace_block(inner, e_brace)
         e_inner = e_block[1:-1].strip()
         e_values = [v.strip().split('=')[0].strip()
                     for v in e_inner.split(',') if v.strip()]
         cls.enums.append(EnumInfo(
            name=e_name, access=e_access, values=e_values
         ))

      info.classes.append(cls)

   return info


# ── Markdown Generation ──────────────────────────────────────────────

def _format_param(p: ParameterInfo) -> str:
   s = f"{p.type_name} {p.name}"
   if p.default_value:
      s += f" = {p.default_value}"
   return s


def _generate_file_md(info: FileInfo, all_filenames: set[str]) -> str:
   """Generate markdown interface map for one file."""
   lines = []
   lines.append(f"# {info.filename}")
   lines.append("")

   if info.namespace:
      lines.append(f"**Namespace:** `{info.namespace}`")
      lines.append("")

   # Dependencies on other project files
   # We infer these from type references in fields, bases, params
   dep_names = set()
   for cls in info.classes:
      for b in cls.base_classes:
         clean = re.sub(r'<.*>', '', b).strip()
         if f"{clean}.cs" in all_filenames and f"{clean}.cs" != info.filename:
            dep_names.add(clean)
      for fld in cls.fields:
         clean = re.sub(r'[\[\]<>,\?\s]', ' ', fld.type_name)
         for token in clean.split():
            if f"{token}.cs" in all_filenames and f"{token}.cs" != info.filename:
               dep_names.add(token)
      for prop in cls.properties:
         clean = re.sub(r'[\[\]<>,\?\s]', ' ', prop.type_name)
         for token in clean.split():
            if f"{token}.cs" in all_filenames and f"{token}.cs" != info.filename:
               dep_names.add(token)
      for meth in cls.methods:
         clean = re.sub(r'[\[\]<>,\?\s]', ' ', meth.return_type)
         for token in clean.split():
            if f"{token}.cs" in all_filenames and f"{token}.cs" != info.filename:
               dep_names.add(token)
         for p in meth.parameters:
            clean = re.sub(r'[\[\]<>,\?\s]', ' ', p.type_name)
            for token in clean.split():
               if f"{token}.cs" in all_filenames and f"{token}.cs" != info.filename:
                  dep_names.add(token)

   info.project_dependencies = sorted(dep_names)

   if info.project_dependencies:
      lines.append(f"**Depends on:** {', '.join(f'`{d}`' for d in info.project_dependencies)}")
      lines.append("")

   # Top-level enums
   for enum in info.top_level_enums:
      lines.append(f"## enum `{enum.name}`")
      lines.append(f"Values: {', '.join(f'`{v}`' for v in enum.values)}")
      lines.append("")

   # Classes
   for cls in info.classes:
      kind = "interface" if cls.is_interface else ("struct" if cls.is_struct else "class")
      mods = []
      if cls.is_abstract:
         mods.append("abstract")
      if cls.is_static:
         mods.append("static")
      if cls.is_partial:
         mods.append("partial")

      header = f"## {cls.access} {''.join(m + ' ' for m in mods)}{kind} `{cls.name}`"
      if cls.base_classes:
         header += f" : {', '.join(f'`{b}`' for b in cls.base_classes)}"
      lines.append(header)
      lines.append("")

      # Nested enums
      for enum in cls.enums:
         lines.append(f"### enum `{enum.name}`")
         lines.append(f"Values: {', '.join(f'`{v}`' for v in enum.values)}")
         lines.append("")

      # Fields
      public_fields = [f for f in cls.fields if f.access == 'public']
      serialized_fields = [f for f in cls.fields if f.is_serialized and f.access != 'public']

      if public_fields:
         lines.append("### Public Fields")
         lines.append("| Type | Name | Notes |")
         lines.append("|------|------|-------|")
         for fld in public_fields:
            notes = []
            if fld.is_static:
               notes.append("static")
            if fld.is_readonly:
               notes.append("readonly")
            if fld.default_value:
               notes.append(f"= {fld.default_value.strip()}")
            lines.append(f"| `{fld.type_name}` | `{fld.name}` | {', '.join(notes)} |")
         lines.append("")

      if serialized_fields:
         lines.append("### Serialized Fields (Inspector)")
         lines.append("| Type | Name | Notes |")
         lines.append("|------|------|-------|")
         for fld in serialized_fields:
            notes = []
            if fld.default_value:
               notes.append(f"= {fld.default_value.strip()}")
            lines.append(f"| `{fld.type_name}` | `{fld.name}` | {', '.join(notes)} |")
         lines.append("")

      # Properties
      public_props = [p for p in cls.properties if p.access == 'public']
      if public_props:
         lines.append("### Properties")
         lines.append("| Type | Name | get | set | Notes |")
         lines.append("|------|------|-----|-----|-------|")
         for prop in public_props:
            notes = []
            if prop.is_static:
               notes.append("static")
            lines.append(
               f"| `{prop.type_name}` | `{prop.name}` "
               f"| {'✓' if prop.has_getter else '—'} "
               f"| {'✓' if prop.has_setter else '—'} "
               f"| {', '.join(notes)} |"
            )
         lines.append("")

      # Methods — split into lifecycle, public API, and overridable
      # Only detect Unity lifecycle for MonoBehaviour-derived classes
      is_unity_class = any(
         b.strip() in ('MonoBehaviour', 'NetworkBehaviour', 'ScriptableObject', 'Editor', 'EditorWindow')
         for b in cls.base_classes
      )
      lifecycle = [m for m in cls.methods if is_unity_class and _is_unity_lifecycle(m.name)]
      public_api = [m for m in cls.methods
                    if m.access == 'public'
                    and not (is_unity_class and _is_unity_lifecycle(m.name))]
      overridable = [m for m in cls.methods
                     if m.access in ('protected', 'internal')
                     and (m.is_virtual or m.is_abstract)]

      if lifecycle:
         lines.append(f"### Unity Lifecycle")
         lines.append(f"`{'`, `'.join(m.name for m in lifecycle)}`")
         lines.append("")

      if public_api:
         lines.append("### Public Methods")
         for meth in public_api:
            mods = []
            if meth.is_static:
               mods.append("static")
            if meth.is_async:
               mods.append("async")
            if meth.is_coroutine:
               mods.append("coroutine")
            if meth.is_virtual:
               mods.append("virtual")
            if meth.is_override:
               mods.append("override")

            params_str = ", ".join(_format_param(p) for p in meth.parameters)
            mod_str = f" *[{', '.join(mods)}]*" if mods else ""
            lines.append(f"- `{meth.return_type} {meth.name}({params_str})`{mod_str}")
         lines.append("")

      if overridable:
         lines.append("### Overridable (protected/internal)")
         for meth in overridable:
            mods = []
            if meth.is_virtual:
               mods.append("virtual")
            if meth.is_abstract:
               mods.append("abstract")
            params_str = ", ".join(_format_param(p) for p in meth.parameters)
            mod_str = f" *[{', '.join(mods)}]*" if mods else ""
            lines.append(f"- `{meth.return_type} {meth.name}({params_str})`{mod_str}")
         lines.append("")

   return "\n".join(lines)


def _generate_readme(all_files: list[FileInfo], output_dir: str) -> str:
   """Generate the global README consolidation."""
   lines = []
   lines.append("# Project Interface Map")
   lines.append("")
   lines.append(f"Auto-generated API surface for **{len(all_files)}** C# scripts.")
   lines.append("Each linked file contains the public API, serialized fields, dependencies,")
   lines.append("and Unity lifecycle hooks — enough for an AI to interface with the original source.")
   lines.append("")

   # Build dependency graph info
   class_to_file: dict[str, str] = {}
   for fi in all_files:
      for cls in fi.classes:
         class_to_file[cls.name] = fi.filename

   # --- Index table ---
   lines.append("## Script Index")
   lines.append("")
   lines.append("| Script | Classes | Base | Depends On |")
   lines.append("|--------|---------|------|------------|")

   for fi in sorted(all_files, key=lambda f: f.filename.lower()):
      md_name = fi.filename.replace('.cs', '.md')
      classes = ", ".join(f"`{c.name}`" for c in fi.classes)
      bases = set()
      for c in fi.classes:
         for b in c.base_classes:
            bases.add(b)
      bases_str = ", ".join(f"`{b}`" for b in sorted(bases)) if bases else "—"
      deps_str = ", ".join(f"`{d}`" for d in fi.project_dependencies) if fi.project_dependencies else "—"
      lines.append(f"| [{fi.filename}]({md_name}) | {classes} | {bases_str} | {deps_str} |")

   lines.append("")

   # --- Dependency summary ---
   lines.append("## Dependency Graph (Adjacency)")
   lines.append("```")
   for fi in sorted(all_files, key=lambda f: f.filename.lower()):
      if fi.project_dependencies:
         for dep in fi.project_dependencies:
            lines.append(f"{fi.filename.replace('.cs','')} -> {dep}")
   lines.append("```")
   lines.append("")

   # --- Consolidated quick-ref of all public methods ---
   lines.append("## All Public Methods (Quick Reference)")
   lines.append("")
   for fi in sorted(all_files, key=lambda f: f.filename.lower()):
      for cls in fi.classes:
         public_api = [m for m in cls.methods
                       if m.access == 'public' and not _is_unity_lifecycle(m.name)]
         if not public_api:
            continue
         lines.append(f"### `{cls.name}`")
         for meth in public_api:
            params_str = ", ".join(_format_param(p) for p in meth.parameters)
            lines.append(f"- `{meth.return_type} {meth.name}({params_str})`")
         lines.append("")

   # --- All enums ---
   all_enums = []
   for fi in all_files:
      for e in fi.top_level_enums:
         all_enums.append((fi.filename, None, e))
      for cls in fi.classes:
         for e in cls.enums:
            all_enums.append((fi.filename, cls.name, e))

   if all_enums:
      lines.append("## All Enums")
      lines.append("")
      for fname, cls_name, enum in sorted(all_enums, key=lambda x: x[2].name):
         scope = f"{cls_name}." if cls_name else ""
         lines.append(f"- **{scope}{enum.name}**: {', '.join(f'`{v}`' for v in enum.values)}  *(in {fname})*")
      lines.append("")

   return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────

def _main():
   parser = argparse.ArgumentParser(
      description="Generate lightweight .md interface maps from Unity C# scripts."
   )
   parser.add_argument("input_dir", help="Directory containing .cs files (searched recursively)")
   parser.add_argument("output_dir", nargs="?", default=None,
                       help="Output directory (default: <input_dir>/_interface_maps/)")
   args = parser.parse_args()

   input_dir = Path(args.input_dir).resolve()
   if not input_dir.is_dir():
      print(f"Error: '{input_dir}' is not a directory.")
      sys.exit(1)

   output_dir = Path(args.output_dir) if args.output_dir else input_dir / "_interface_maps"
   output_dir.mkdir(parents=True, exist_ok=True)

   # Collect all .cs files
   cs_files = sorted(input_dir.rglob("*.cs"))
   if not cs_files:
      print(f"No .cs files found in '{input_dir}'.")
      sys.exit(0)

   print(f"Found {len(cs_files)} C# files in '{input_dir}'")

   all_filenames = {f.name for f in cs_files}
   all_file_infos: list[FileInfo] = []

   for cs_path in cs_files:
      try:
         fi = _parse_file(str(cs_path))
         all_file_infos.append(fi)
      except Exception as e:
         print(f"  WARN: Failed to parse {cs_path.name}: {e}")

   # Generate per-file markdown
   for fi in all_file_infos:
      md_content = _generate_file_md(fi, all_filenames)
      md_path = output_dir / fi.filename.replace('.cs', '.md')
      with open(md_path, 'w', encoding='utf-8') as f:
         f.write(md_content)

   # Generate global README
   readme_content = _generate_readme(all_file_infos, str(output_dir))
   readme_path = output_dir / "README.md"
   with open(readme_path, 'w', encoding='utf-8') as f:
      f.write(readme_content)

   print(f"Generated {len(all_file_infos)} interface maps + README.md in '{output_dir}'")

   # Token estimate
   total_src = sum(os.path.getsize(str(p)) for p in cs_files)
   total_md = sum(os.path.getsize(str(output_dir / fi.filename.replace('.cs', '.md')))
                  for fi in all_file_infos)
   total_md += os.path.getsize(str(readme_path))
   ratio = (total_md / total_src * 100) if total_src > 0 else 0
   print(f"Source total: {total_src:,} bytes -> Interface maps total: {total_md:,} bytes ({ratio:.1f}%)")


if __name__ == "__main__":
   _main()
