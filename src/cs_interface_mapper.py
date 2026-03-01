#!/usr/bin/env python3
"""
cs_interface_mapper.py  v2.0
Parses Unity C# scripts and produces a SINGLE README.md that gives an AI
everything it needs to interface with the codebase without reading the source.

Output structure:
   1. Architecture Contracts  — extracted from top-of-file doc comments
   2. Runtime Flow            — inferred from lifecycle hooks + call patterns
   3. Shared Constants        — enums, const fields, static readonly fields
   4. Dependency Graph         — who depends on whom
   5. Per-Script Details       — serialized fields, public API with intent
                                 docstrings, properties, lifecycle hooks

Usage:
   python cs_interface_mapper.py <input_dir> [output_dir]

If output_dir is omitted, defaults to <input_dir>/README.md
The script produces exactly ONE file: README.md
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
class ConstInfo:
   """A const or static readonly field — project-wide shared value."""
   name: str
   type_name: str
   value: str
   access: str
   owner_class: str = ""

@dataclass
class FieldInfo:
   name: str
   type_name: str
   access: str
   is_static: bool = False
   is_readonly: bool = False
   is_const: bool = False
   is_serialized: bool = False
   default_value: Optional[str] = None
   header_group: Optional[str] = None
   tooltip: Optional[str] = None

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
   doc_summary: Optional[str] = None

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
   class_doc: Optional[str] = None

@dataclass
class FileInfo:
   filepath: str
   filename: str
   namespace: Optional[str] = None
   usings: list[str] = field(default_factory=list)
   classes: list[ClassInfo] = field(default_factory=list)
   top_level_enums: list[EnumInfo] = field(default_factory=list)
   project_dependencies: list[str] = field(default_factory=list)
   file_doc_comment: Optional[str] = None
   has_editor_guard: bool = False
   raw_source: str = ""


# ── Regex Patterns ───────────────────────────────────────────────────

_RE_USING = re.compile(r'^\s*using\s+([\w.]+)\s*;', re.MULTILINE)
_RE_NAMESPACE = re.compile(r'^\s*namespace\s+([\w.]+)', re.MULTILINE)

_RE_CLASS = re.compile(
   r'(?P<access>public|private|protected|internal)?\s*'
   r'(?P<abstract>abstract\s+)?'
   r'(?P<static>static\s+)?'
   r'(?P<partial>partial\s+)?'
   r'(?P<kind>class|struct|interface)\s+'
   r'(?P<n>\w+)'
   r'(?:<[^>]+>)?'               # generic params
   r'(?:\s*:\s*(?P<bases>[^{]+?))?'
   r'\s*\{'
)

_RE_ENUM = re.compile(
   r'(?P<access>public|private|protected|internal)?\s*'
   r'enum\s+(?P<n>\w+)\s*(?::\s*\w+\s*)?\{'
)

_RE_FIELD = re.compile(
   r'^\s*'
   r'(?P<attrs>(?:\[[\w\s,()="\.]+\]\s*)*)'
   r'(?P<access>public|private|protected|internal)\s+'
   r'(?P<static>static\s+)?'
   r'(?P<const>const\s+)?'
   r'(?P<readonly>readonly\s+)?'
   r'(?P<type>[\w<>\[\],\s\?\.]+?)\s+'
   r'(?P<n>\w+)\s*'
   r'(?:=\s*(?P<default>[^;]+))?\s*;',
   re.MULTILINE
)

_RE_PROPERTY = re.compile(
   r'^\s*'
   r'(?P<access>public|private|protected|internal)\s+'
   r'(?P<static>static\s+)?'
   r'(?P<type>[\w<>\[\],\s\?\.]+?)\s+'
   r'(?P<n>\w+)\s*\{',
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
   r'(?P<n>\w+)\s*'
   r'(?:<[^>]+>)?\s*'           # generic params
   r'\((?P<params>[^)]*)\)',
   re.MULTILINE
)

_RE_SERIALIZE_FIELD = re.compile(r'\[SerializeField\]')
_RE_HEADER = re.compile(r'\[Header\(\s*"([^"]+)"\s*\)\]')
_RE_TOOLTIP = re.compile(r'\[Tooltip\(\s*"([^"]+)"\s*\)\]')
_RE_EDITOR_GUARD = re.compile(r'#if\s+UNITY_EDITOR')


# ── Helpers ──────────────────────────────────────────────────────────

def _strip_comments(src: str) -> str:
   """Remove single-line and multi-line comments for parsing.
   Returns the stripped source (used for structural parsing only)."""
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


def _extract_file_doc(raw_src: str) -> Optional[str]:
   """Extract the top-of-file doc comment (before any using/namespace).

   Looks for a block comment or consecutive // lines at the very top.
   This is where architecture contracts and design notes tend to live."""
   lines = raw_src.lstrip('\ufeff').split('\n')
   doc_lines = []
   in_block = False

   for line in lines:
      stripped = line.strip()
      # Stop at first code line (using, namespace, attribute, class, etc.)
      if not in_block and stripped and not stripped.startswith('//') and not stripped.startswith('/*') and not stripped.startswith('*'):
         break
      # Block comment
      if stripped.startswith('/*'):
         in_block = True
         content = stripped[2:].lstrip('* ')
         if content:
            doc_lines.append(content)
         if '*/' in stripped:
            in_block = False
            if doc_lines:
               doc_lines[-1] = doc_lines[-1].split('*/')[0].rstrip()
         continue
      if in_block:
         if '*/' in stripped:
            content = stripped.split('*/')[0].lstrip('* ').rstrip()
            if content:
               doc_lines.append(content)
            in_block = False
            continue
         content = stripped.lstrip('* ')
         doc_lines.append(content)
         continue
      # /// lines
      if stripped.startswith('///'):
         content = stripped[3:].strip()
         content = re.sub(r'</?summary>', '', content).strip()
         if content:
            doc_lines.append(content)
         continue
      # // lines at top of file
      if stripped.startswith('//'):
         content = stripped[2:].strip()
         if content:
            doc_lines.append(content)
         continue
      # Empty lines are fine as separators
      if not stripped:
         if doc_lines:
            doc_lines.append("")
         continue

   # Trim trailing empty lines
   while doc_lines and not doc_lines[-1]:
      doc_lines.pop()

   if not doc_lines:
      return None

   result = '\n'.join(doc_lines)
   if len(result) < 20:
      return None
   return result


def _extract_doc_for_member(raw_src: str, member_name: str) -> Optional[str]:
   """Extract the /// or /** doc comment immediately preceding a member.

   Strategy: find the declaration line containing the member name,
   then walk backwards to collect /// or /** comment lines.
   Returns a single cleaned-up summary string, or None."""
   # Find declaration lines containing this member name as a whole word
   decl_pattern = re.compile(
      r'^[ \t]*(?:\[.*?\]\s*)*'
      r'(?:public|private|protected|internal)\s+'
      r'[^;\n]*?\b' + re.escape(member_name) + r'\b',
      re.MULTILINE
   )

   lines = raw_src.split('\n')

   for match in decl_pattern.finditer(raw_src):
      # Find which line number this declaration is on
      line_num = raw_src[:match.start()].count('\n')

      # Walk backwards from the line before the declaration
      # to collect /// or /** comment lines
      doc_lines = []
      # Skip attribute lines like [SerializeField], [Header(...)], etc.
      i = line_num - 1
      while i >= 0:
         stripped = lines[i].strip()
         # Skip blank lines between doc comment and declaration
         if not stripped:
            if doc_lines:
               break  # blank line after doc means we're done
            i -= 1
            continue
         # Skip attribute lines
         if stripped.startswith('[') and stripped.endswith(']'):
            i -= 1
            continue
         # Collect /// lines
         if stripped.startswith('///'):
            content = stripped[3:].strip()
            content = re.sub(r'</?summary>', '', content).strip()
            content = re.sub(r'</?remarks>', '', content).strip()
            content = re.sub(r'<param\s+name="[^"]*">', '', content).strip()
            content = re.sub(r'</param>', '', content).strip()
            content = re.sub(r'</?returns>', '', content).strip()
            if content:
               doc_lines.insert(0, content)
            i -= 1
            continue
         # Collect /** ... */ block (single or multi-line)
         if '*/' in stripped:
            block_lines = []
            while i >= 0:
               line_text = lines[i].strip()
               block_lines.insert(0, line_text)
               if '/*' in line_text:
                  break
               i -= 1
            block_text = ' '.join(block_lines)
            # Strip /** and */
            block_text = re.sub(r'/\*\*?', '', block_text)
            block_text = re.sub(r'\*/', '', block_text)
            block_text = block_text.strip().strip('* ').strip()
            if block_text:
               doc_lines.insert(0, block_text)
            break
         # Not a comment or attribute — stop
         break

      if doc_lines:
         return ' '.join(doc_lines)

   return None


def _extract_class_doc(raw_src: str, class_name: str) -> Optional[str]:
   """Extract doc comment for a class/struct/interface declaration."""
   return _extract_doc_for_member(raw_src, class_name)


# ── Parser ───────────────────────────────────────────────────────────

def _parse_file(filepath: str) -> FileInfo:
   """Parse a single C# file and extract its interface surface."""
   with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
      raw_src = f.read()

   src = _strip_comments(raw_src)
   info = FileInfo(
      filepath=filepath,
      filename=os.path.basename(filepath),
      raw_source=raw_src,
   )

   # File-level doc comment
   info.file_doc_comment = _extract_file_doc(raw_src)

   # Editor guard detection
   info.has_editor_guard = bool(_RE_EDITOR_GUARD.search(raw_src))

   # Usings
   info.usings = _RE_USING.findall(src)

   # Namespace
   ns_match = _RE_NAMESPACE.search(src)
   if ns_match:
      info.namespace = ns_match.group(1)

   # Top-level enums
   first_class = _RE_CLASS.search(src)
   enum_boundary = first_class.start() if first_class else len(src)
   for m in _RE_ENUM.finditer(src):
      if m.start() >= enum_boundary:
         break
      access = m.group('access') or 'internal'
      name = m.group('n')
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
         if current and not current.startswith('where'):
            bases.append(current.split(' where ')[0].strip())

      cls = ClassInfo(
         name=m.group('n'),
         access=m.group('access') or 'internal',
         base_classes=bases,
         is_abstract=bool(m.group('abstract')),
         is_static=bool(m.group('static')),
         is_partial=bool(m.group('partial')),
         is_struct=(m.group('kind') == 'struct'),
         is_interface=(m.group('kind') == 'interface'),
         class_doc=_extract_class_doc(raw_src, m.group('n')),
      )

      # Track current [Header] group for serialized field grouping
      current_header = None

      # Fields
      for fm in _RE_FIELD.finditer(inner):
         access = fm.group('access')
         attrs = fm.group('attrs') or ''
         is_serialized = bool(_RE_SERIALIZE_FIELD.search(attrs))
         is_const = bool(fm.group('const'))
         is_static = bool(fm.group('static'))
         is_readonly = bool(fm.group('readonly'))

         type_name = fm.group('type').strip()
         if type_name in ('return', 'yield', 'var', 'throw', 'new'):
            continue

         # Extract [Header] and [Tooltip] from attributes
         header_match = _RE_HEADER.search(attrs)
         if header_match:
            current_header = header_match.group(1)
         tooltip_match = _RE_TOOLTIP.search(attrs)
         tooltip = tooltip_match.group(1) if tooltip_match else None

         # Capture public fields, serialized private fields, AND const/static-readonly
         should_include = (
            access == 'public'
            or is_serialized
            or (is_const and access in ('public', 'internal'))
            or (is_static and is_readonly and access in ('public', 'internal'))
         )
         if not should_include:
            continue

         cls.fields.append(FieldInfo(
            name=fm.group('n'),
            type_name=type_name,
            access=access,
            is_static=is_static,
            is_readonly=is_readonly,
            is_const=is_const,
            is_serialized=is_serialized,
            default_value=fm.group('default'),
            header_group=current_header if is_serialized else None,
            tooltip=tooltip if is_serialized else None,
         ))

      # Properties (public only)
      for pm in _RE_PROPERTY.finditer(inner):
         if pm.group('access') != 'public':
            continue
         prop_name = pm.group('n')
         type_name = pm.group('type').strip()
         if type_name in ('return', 'yield', 'var', 'throw', 'new',
                          'class', 'enum', 'struct', 'interface', 'event'):
            continue
         known_type_names = {e.name for e in cls.enums}
         if prop_name in known_type_names:
            continue
         line_start = inner.rfind('\n', 0, pm.start()) + 1
         line_text = inner[line_start:pm.end()].strip()
         if re.match(
            r'(?:public|private|protected|internal)\s+'
            r'(?:enum|class|struct|interface)\s+',
            line_text
         ):
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

      # Methods
      for mm in _RE_METHOD.finditer(inner):
         access = mm.group('access')
         is_virtual = bool(mm.group('virtual'))
         is_override = bool(mm.group('override'))
         is_abstract = bool(mm.group('abstract'))
         name = mm.group('n')
         ret = mm.group('return').strip()

         if access == 'private':
            continue
         if access == 'internal' and not (is_virtual or is_override or is_abstract):
            continue
         if access == 'protected' and not (is_virtual or is_override or is_abstract):
            continue

         is_coroutine = (ret == 'IEnumerator')
         doc = _extract_doc_for_member(raw_src, name)

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
            doc_summary=doc,
         ))

      # Nested enums
      for em in _RE_ENUM.finditer(inner):
         e_access = em.group('access') or 'internal'
         if e_access not in ('public', 'internal'):
            continue
         e_name = em.group('n')
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


# ── Dependency Resolution ────────────────────────────────────────────

def _resolve_dependencies(all_files: list[FileInfo], all_filenames: set[str]):
   """Resolve project-internal dependencies for each file.
   Mutates each FileInfo.project_dependencies in place."""
   for fi in all_files:
      dep_names = set()
      for cls in fi.classes:
         # Base classes
         for b in cls.base_classes:
            clean = re.sub(r'<.*>', '', b).strip()
            if f"{clean}.cs" in all_filenames and f"{clean}.cs" != fi.filename:
               dep_names.add(clean)
         # Fields
         for fld in cls.fields:
            clean = re.sub(r'[\[\]<>,\?\s]', ' ', fld.type_name)
            for token in clean.split():
               if f"{token}.cs" in all_filenames and f"{token}.cs" != fi.filename:
                  dep_names.add(token)
         # Properties
         for prop in cls.properties:
            clean = re.sub(r'[\[\]<>,\?\s]', ' ', prop.type_name)
            for token in clean.split():
               if f"{token}.cs" in all_filenames and f"{token}.cs" != fi.filename:
                  dep_names.add(token)
         # Method return types and parameters
         for meth in cls.methods:
            clean = re.sub(r'[\[\]<>,\?\s]', ' ', meth.return_type)
            for token in clean.split():
               if f"{token}.cs" in all_filenames and f"{token}.cs" != fi.filename:
                  dep_names.add(token)
            for p in meth.parameters:
               clean = re.sub(r'[\[\]<>,\?\s]', ' ', p.type_name)
               for token in clean.split():
                  if f"{token}.cs" in all_filenames and f"{token}.cs" != fi.filename:
                     dep_names.add(token)
      fi.project_dependencies = sorted(dep_names)


# ── Runtime Flow Inference ───────────────────────────────────────────

def _infer_runtime_flow(all_files: list[FileInfo]) -> list[str]:
   """Infer edit-time and play-time execution flow from lifecycle hooks,
   [MenuItem] attributes, and class hierarchies.

   Returns a list of markdown lines describing the flow."""
   editor_scripts = []
   runtime_scripts = []

   for fi in all_files:
      is_editor = fi.has_editor_guard or any(
         any(b.strip() in ('Editor', 'EditorWindow', 'AssetPostprocessor')
             for b in cls.base_classes)
         for cls in fi.classes
      )
      if '[MenuItem' in fi.raw_source or '[InitializeOnLoad' in fi.raw_source:
         is_editor = True

      for cls in fi.classes:
         entry = {
            'file': fi.filename,
            'class': cls.name,
            'bases': cls.base_classes,
            'lifecycle': [],
            'public_methods': [],
            'is_editor': is_editor,
            'doc': cls.class_doc,
         }
         for m in cls.methods:
            if _is_unity_lifecycle(m.name):
               entry['lifecycle'].append(m.name)
            if m.access == 'public' and not _is_unity_lifecycle(m.name):
               entry['public_methods'].append(m.name)

         if is_editor:
            editor_scripts.append(entry)
         else:
            runtime_scripts.append(entry)

   flow_lines = []

   if editor_scripts:
      flow_lines.append("**Edit-time (Editor scripts):**")
      for e in editor_scripts:
         methods = ', '.join(f'`{m}`' for m in e['public_methods']) if e['public_methods'] else '*(no public API)*'
         base_str = f" : {', '.join(e['bases'])}" if e['bases'] else ""
         line = f"- `{e['class']}`{base_str} — {methods}"
         if e['doc']:
            line += f"  — *{e['doc'][:80]}*"
         flow_lines.append(line)

   if runtime_scripts:
      if editor_scripts:
         flow_lines.append("")
      flow_lines.append("**Play-time (Runtime scripts):**")

      # Sort: Awake/Start first, then Update-family, then the rest
      def _lifecycle_order(entry):
         hooks = entry['lifecycle']
         if 'Awake' in hooks:
            return 0
         if 'Start' in hooks:
            return 1
         if 'OnEnable' in hooks:
            return 2
         if any(h in hooks for h in ('Update', 'FixedUpdate', 'LateUpdate')):
            return 3
         return 4

      for e in sorted(runtime_scripts, key=_lifecycle_order):
         hooks = ', '.join(f'`{h}`' for h in e['lifecycle']) if e['lifecycle'] else '*(no lifecycle)*'
         methods = ', '.join(f'`{m}`' for m in e['public_methods']) if e['public_methods'] else ''
         base_str = f" : {', '.join(e['bases'])}" if e['bases'] else ""
         parts = [f"hooks: {hooks}"]
         if methods:
            parts.append(f"API: {methods}")
         flow_lines.append(f"- `{e['class']}`{base_str} — {'; '.join(parts)}")

   return flow_lines


# ── Markdown Generation ──────────────────────────────────────────────

def _format_param(p: ParameterInfo) -> str:
   s = f"{p.type_name} {p.name}"
   if p.default_value:
      s += f" = {p.default_value}"
   return s


def _generate_class_section(cls: ClassInfo, fi: FileInfo) -> list[str]:
   """Generate the detailed per-class section for the README."""
   lines = []

   kind = "interface" if cls.is_interface else ("struct" if cls.is_struct else "class")
   mods = []
   if cls.is_abstract:
      mods.append("abstract")
   if cls.is_static:
      mods.append("static")
   if cls.is_partial:
      mods.append("partial")

   header = f"#### {''.join(m + ' ' for m in mods)}{kind} `{cls.name}`"
   if cls.base_classes:
      header += f" : {', '.join(f'`{b}`' for b in cls.base_classes)}"
   lines.append(header)

   if cls.class_doc:
      # Collapse multi-line doc to single blockquote
      doc_oneline = ' '.join(cls.class_doc.split('\n')).strip()
      lines.append(f"> {doc_oneline}")
   lines.append("")

   # Nested enums
   for enum in cls.enums:
      lines.append(f"**enum `{enum.name}`:** {', '.join(f'`{v}`' for v in enum.values)}")
      lines.append("")

   # Serialized fields (grouped by [Header] if present)
   serialized = [f for f in cls.fields if f.is_serialized and f.access != 'public']
   if serialized:
      lines.append("**Serialized Fields (Inspector):**")
      current_group = None
      for fld in serialized:
         if fld.header_group and fld.header_group != current_group:
            current_group = fld.header_group
            lines.append(f"  *— {current_group} —*")
         notes = []
         if fld.default_value:
            notes.append(f"= `{fld.default_value.strip()}`")
         if fld.tooltip:
            notes.append(f'"{fld.tooltip}"')
         note_str = f"  {' '.join(notes)}" if notes else ""
         lines.append(f"- `{fld.type_name}` **{fld.name}**{note_str}")
      lines.append("")

   # Public fields (non-const, non-static-readonly — those go in Constants)
   public_fields = [f for f in cls.fields
                    if f.access == 'public' and not f.is_const
                    and not (f.is_static and f.is_readonly)]
   if public_fields:
      lines.append("**Public Fields:**")
      for fld in public_fields:
         notes = []
         if fld.is_static:
            notes.append("static")
         if fld.is_readonly:
            notes.append("readonly")
         if fld.default_value:
            notes.append(f"= `{fld.default_value.strip()}`")
         note_str = f"  ({', '.join(notes)})" if notes else ""
         lines.append(f"- `{fld.type_name}` **{fld.name}**{note_str}")
      lines.append("")

   # Properties
   public_props = [p for p in cls.properties if p.access == 'public']
   if public_props:
      lines.append("**Properties:**")
      for prop in public_props:
         access_parts = []
         if prop.has_getter:
            access_parts.append("get")
         if prop.has_setter:
            access_parts.append("set")
         access_str = "/".join(access_parts) if access_parts else "?"
         static_str = " static" if prop.is_static else ""
         lines.append(f"- `{prop.type_name}` **{prop.name}** {{ {access_str} }}{static_str}")
      lines.append("")

   # Unity lifecycle hooks
   is_unity_class = any(
      b.strip() in ('MonoBehaviour', 'NetworkBehaviour', 'ScriptableObject',
                     'Editor', 'EditorWindow')
      for b in cls.base_classes
   )
   lifecycle = [m for m in cls.methods
                if is_unity_class and _is_unity_lifecycle(m.name)]
   if lifecycle:
      lines.append(f"**Lifecycle:** `{'`, `'.join(m.name for m in lifecycle)}`")
      lines.append("")

   # Public methods
   public_api = [m for m in cls.methods
                 if m.access == 'public'
                 and not (is_unity_class and _is_unity_lifecycle(m.name))]
   if public_api:
      lines.append("**Public Methods:**")
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
         sig = f"- `{meth.return_type} {meth.name}({params_str})`{mod_str}"
         if meth.doc_summary:
            sig += f"  — {meth.doc_summary}"
         lines.append(sig)
      lines.append("")

   # Overridable methods
   overridable = [m for m in cls.methods
                  if m.access in ('protected', 'internal')
                  and (m.is_virtual or m.is_abstract)]
   if overridable:
      lines.append("**Overridable:**")
      for meth in overridable:
         mods = []
         if meth.is_virtual:
            mods.append("virtual")
         if meth.is_abstract:
            mods.append("abstract")
         params_str = ", ".join(_format_param(p) for p in meth.parameters)
         mod_str = f" *[{', '.join(mods)}]*" if mods else ""
         sig = f"- `{meth.return_type} {meth.name}({params_str})`{mod_str}"
         if meth.doc_summary:
            sig += f"  — {meth.doc_summary}"
         lines.append(sig)
      lines.append("")

   return lines


def _generate_readme(all_files: list[FileInfo]) -> str:
   """Generate the single consolidated README.md."""
   lines = []
   lines.append("# Project Interface Map")
   lines.append("")
   lines.append(f"Auto-generated from **{len(all_files)}** C# scripts.")
   lines.append("Contains everything an AI needs to interface with this codebase")
   lines.append("without reading the original source files.")
   lines.append("")

   # ── 1. Architecture Contracts ─────────────────────────────────────
   contracts = []
   for fi in sorted(all_files, key=lambda f: f.filename.lower()):
      if fi.file_doc_comment:
         contracts.append((fi.filename, fi.file_doc_comment))

   if contracts:
      lines.append("## Architecture Contracts")
      lines.append("")
      for fname, doc in contracts:
         lines.append(f"### From `{fname}`")
         for dline in doc.split('\n'):
            stripped = dline.strip()
            # Skip lines that just echo the filename
            if stripped == fname or stripped == fname.replace('.cs', ''):
               continue
            lines.append(f"> {dline}" if stripped else ">")
         lines.append("")

   # ── 2. Runtime Flow ───────────────────────────────────────────────
   flow_lines = _infer_runtime_flow(all_files)
   if flow_lines:
      lines.append("## Runtime Flow")
      lines.append("")
      for fl in flow_lines:
         lines.append(fl)
      lines.append("")

   # ── 3. Shared Constants & Enums ───────────────────────────────────
   all_consts: list[ConstInfo] = []
   all_enums: list[tuple[str, Optional[str], EnumInfo]] = []

   for fi in all_files:
      for e in fi.top_level_enums:
         all_enums.append((fi.filename, None, e))
      for cls in fi.classes:
         for e in cls.enums:
            all_enums.append((fi.filename, cls.name, e))
         for fld in cls.fields:
            if fld.is_const or (fld.is_static and fld.is_readonly):
               if fld.access in ('public', 'internal'):
                  all_consts.append(ConstInfo(
                     name=fld.name,
                     type_name=fld.type_name,
                     value=fld.default_value.strip() if fld.default_value else "?",
                     access=fld.access,
                     owner_class=cls.name,
                  ))

   if all_enums or all_consts:
      lines.append("## Shared Constants & Enums")
      lines.append("")

      if all_enums:
         for fname, cls_name, enum in sorted(all_enums, key=lambda x: x[2].name):
            scope = f"{cls_name}." if cls_name else ""
            vals = ', '.join(f'`{v}`' for v in enum.values)
            lines.append(f"- **enum {scope}{enum.name}:** {vals}  *(in {fname})*")
         lines.append("")

      if all_consts:
         lines.append("| Owner | Type | Name | Value |")
         lines.append("|-------|------|------|-------|")
         for c in sorted(all_consts, key=lambda x: (x.owner_class, x.name)):
            # Collapse multi-line values to single line for table
            val = ' '.join(c.value.split())
            # Truncate very long values (e.g. large array initializers)
            if len(val) > 120:
               val = val[:117] + "..."
            lines.append(
               f"| `{c.owner_class}` | `{c.type_name}` "
               f"| `{c.name}` | `{val}` |"
            )
         lines.append("")

   # ── 4. Dependency Graph ───────────────────────────────────────────
   has_deps = any(fi.project_dependencies for fi in all_files)
   if has_deps:
      lines.append("## Dependency Graph")
      lines.append("```")
      for fi in sorted(all_files, key=lambda f: f.filename.lower()):
         if fi.project_dependencies:
            for dep in fi.project_dependencies:
               src_name = fi.filename.replace('.cs', '')
               lines.append(f"{src_name} -> {dep}")
      lines.append("```")
      lines.append("")

   # ── 5. Script Index ───────────────────────────────────────────────
   lines.append("## Script Index")
   lines.append("")
   lines.append("| Script | Classes | Base | Depends On | Editor? |")
   lines.append("|--------|---------|------|------------|---------|")

   for fi in sorted(all_files, key=lambda f: f.filename.lower()):
      classes = ", ".join(f"`{c.name}`" for c in fi.classes)
      bases = set()
      for c in fi.classes:
         for b in c.base_classes:
            bases.add(b)
      bases_str = ", ".join(f"`{b}`" for b in sorted(bases)) if bases else "—"
      deps_str = (", ".join(f"`{d}`" for d in fi.project_dependencies)
                  if fi.project_dependencies else "—")
      editor_str = "✓" if fi.has_editor_guard else "—"
      lines.append(
         f"| `{fi.filename}` | {classes} "
         f"| {bases_str} | {deps_str} | {editor_str} |"
      )

   lines.append("")

   # ── 6. Per-Script Detail Sections ─────────────────────────────────
   lines.append("## Script Details")
   lines.append("")

   for fi in sorted(all_files, key=lambda f: f.filename.lower()):
      lines.append(f"### `{fi.filename}`")

      meta_parts = []
      if fi.namespace:
         meta_parts.append(f"Namespace: `{fi.namespace}`")
      if fi.project_dependencies:
         deps = ', '.join(f'`{d}`' for d in fi.project_dependencies)
         meta_parts.append(f"Depends on: {deps}")
      if fi.has_editor_guard:
         meta_parts.append("*Editor-only (`#if UNITY_EDITOR`)*")
      if meta_parts:
         lines.append(" · ".join(meta_parts))

      lines.append("")

      for cls in fi.classes:
         class_lines = _generate_class_section(cls, fi)
         lines.extend(class_lines)

   return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────

def _main():
   parser = argparse.ArgumentParser(
      description="Generate a single README.md interface map from Unity C# scripts."
   )
   parser.add_argument("input_dir", default='.',
                       help="Directory containing .cs files (searched recursively)")
   parser.add_argument("output_dir", nargs="?", default=None,
                       help="Output directory (default: <input_dir>)")
   args = parser.parse_args()

   input_dir = Path(args.input_dir).resolve()
   if not input_dir.is_dir():
      print(f"Error: '{input_dir}' is not a directory.")
      sys.exit(1)

   output_dir = Path(args.output_dir) if args.output_dir else input_dir
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

   # Resolve cross-file dependencies
   _resolve_dependencies(all_file_infos, all_filenames)

   # Generate single README
   readme_content = _generate_readme(all_file_infos)
   readme_path = output_dir / "README.md"
   with open(readme_path, 'w', encoding='utf-8') as f:
      f.write(readme_content)

   print(f"Generated README.md in '{output_dir}'")

   # Size estimate
   total_src = sum(os.path.getsize(str(p)) for p in cs_files)
   total_md = os.path.getsize(str(readme_path))
   ratio = (total_md / total_src * 100) if total_src > 0 else 0
   print(f"Source: {total_src:,} bytes -> README: {total_md:,} bytes ({ratio:.1f}%)")


if __name__ == "__main__":
   _main()
