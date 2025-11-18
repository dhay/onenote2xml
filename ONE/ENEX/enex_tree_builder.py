#   Copyright 2024 Alexandre Grigoriev
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

from __future__ import annotations
from xml.etree import ElementTree as ET
import datetime
from ..base_types import *
from ..NOTE.object_tree_builder import *

class EnexRevisionTreeBuilderCtx(RevisionBuilderCtx):
    """Context for building a single revision into ENEX format."""

    def __init__(self, property_set_factory, revision, object_space_ctx):
        self.include_oids = getattr(object_space_ctx.options, 'include_oids', False)
        super().__init__(property_set_factory, revision, object_space_ctx)
        return

    def MakeJsonTree(self):
        """Build JSON tree for conversion to ENEX."""
        obj = {}

        for role in self.revision_roles:
            role_tree = self.GetRootObject(role)
            obj.update(role_tree.MakeJsonNode(self))

        if self.is_encrypted:
            obj['IsEncrypted'] = True

        return obj

class EnexObjectSpaceBuilderCtx(ObjectSpaceBuilderCtx):
    """Context for building object space into ENEX format."""
    REVISION_BUILDER = EnexRevisionTreeBuilderCtx

    def MakeRootJsonTree(self):
        return self.root_revision_ctx.MakeJsonTree()

class EnexTreeBuilder(ObjectTreeBuilder):
    """Builder for converting OneNote data to ENEX format."""
    OBJECT_SPACE_BUILDER = EnexObjectSpaceBuilderCtx

    def __init__(self, onestore, property_set_factory, options=None):
        # Store onestore so we can use it later
        self.onestore = onestore
        # Call parent init
        super().__init__(onestore, property_set_factory, options)

    def BuildEnexTree(self, root_tree_name:str, options):
        """Build complete ENEX document tree."""
        # Use the JSON tree builder to get the full JSON representation with all metadata
        from ..JSON.json_tree_builder import JsonTreeBuilder
        from ..JSON.json_property_set_factory import OneNotebookJsonPropertySetFactory
        from types import SimpleNamespace

        # Create options with verbosity 5 to get all attributes including timestamps
        # Verbosity levels: 5 = all objects and attributes
        json_options = SimpleNamespace()
        json_options.verbosity = 6
        # json_options.include_oids = getattr(options, 'include_oids', False)
        # json_options.all_revisions = False
        # json_options.timestamp = None

        # Create a JSON builder with the same onestore
        json_builder = JsonTreeBuilder(self.onestore, OneNotebookJsonPropertySetFactory, json_options)

        # Build the full JSON tree
        json_tree = json_builder.BuildJsonTree(root_tree_name, json_options)

        # Create ENEX root element
        enex_root = ET.Element('en-export')
        enex_root.set('export-date', self._format_datetime(datetime.datetime.now()))
        enex_root.set('application', 'OneNote')
        enex_root.set('version', '4.0')

        # Extract pages from the JSON tree
        # The structure is: { 'type': 'NotebookSection', 'pages': { 'GUID1': {...}, 'GUID2': {...}, ... } }
        if 'pages' in json_tree:
            for page_id, page_data in json_tree['pages'].items():
                note_elem = self._convert_page_to_note(page_data)
                if note_elem is not None:
                    enex_root.append(note_elem)

        return enex_root

    def _format_datetime(self, dt):
        """Format datetime to ENEX format: yyyymmddThhmmssZ"""
        if isinstance(dt, (int, float)):
            # Convert from Windows FILETIME (100-nanosecond intervals since Jan 1, 1601)
            # to Unix timestamp (seconds since Jan 1, 1970)
            FILETIME_EPOCH_DIFF = 116444736000000000  # 100-nanosecond intervals between 1601 and 1970
            unix_timestamp = (dt - FILETIME_EPOCH_DIFF) / 10000000.0
            dt = datetime.datetime.utcfromtimestamp(unix_timestamp)
        return dt.strftime('%Y%m%dT%H%M%SZ')

    def _convert_page_to_note(self, page_data):
        """Convert a OneNote page to an Evernote note element."""
        note = ET.Element('note')

        # Extract title from CachedTitleString
        title_text = page_data.get('CachedTitleString', 'Untitled')
        title = ET.SubElement(note, 'title')
        title.text = title_text

        # Build ENML content
        content_html = self._build_enml_content(page_data)
        content = ET.SubElement(note, 'content')
        content.text = content_html

        # Extract creation timestamp from TopologyCreationTimeStamp
        # Note: These fields may not be present depending on JSON verbosity settings
        created_time = page_data.get('TopologyCreationTimeStamp')
        if created_time:
            created = ET.SubElement(note, 'created')
            created.text = self._format_datetime(created_time)

        # Extract modification timestamp from LastModifiedTimeStamp
        updated_time = page_data.get('LastModifiedTimeStamp')
        if updated_time:
            updated = ET.SubElement(note, 'updated')
            updated.text = self._format_datetime(updated_time)

        # Extract author from AuthorMostRecent
        author_data = page_data.get('AuthorMostRecent')
        if author_data and isinstance(author_data, dict):
            author_name = author_data.get('Author')
            if author_name:
                note_attrs = ET.SubElement(note, 'note-attributes')
                author = ET.SubElement(note_attrs, 'author')
                author.text = author_name

        # Extract and add resources (images, attachments)
        resources = self._extract_resources(page_data)
        for resource_elem in resources:
            note.append(resource_elem)

        return note

    def _build_enml_content(self, page_data):
        """Build ENML content from page data."""
        # ENML content must be wrapped in proper XML structure
        enml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
        enml_parts.append('<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">')
        enml_parts.append('<en-note>')

        # Extract content from page
        content_html = self._extract_content(page_data)
        enml_parts.append(content_html)

        enml_parts.append('</en-note>')

        return '\n'.join(enml_parts)

    def _extract_content(self, page_data):
        """Extract and format content from page data.

        Walk the ContentChildNodes array (typically has one element).
        Then recursively walk ElementChildNodes looking for:
        - ListNodes (indicates a list or nested list)
        - ContentChildNodes (contains sub-content)
        - RichEditTextUnicode (the actual text)
        Styling comes from ParagraphStyle and TextRunFormatting at the same level as RichEditTextUnicode.
        """
        html_parts = []

        # Get the ContentChildNodes array (typically has one element)
        content_nodes = page_data.get('ContentChildNodes', [])
        if not content_nodes:
            return '<div>No content</div>'

        # Process the first (and typically only) ContentChildNodes element
        for content_node in content_nodes:
            if not isinstance(content_node, dict):
                continue

            # Get the ElementChildNodes array to walk
            element_nodes = content_node.get('ElementChildNodes', [])

            # Recursively process each element node
            html_parts.extend(self._process_element_list(element_nodes))
            # for element_node in element_nodes:
            #     html_parts.extend(self._process_element_node(element_node))

        return '\n'.join(html_parts) if html_parts else '<div>No content</div>'

    def _process_element_list(self, element_nodes, depth=-1):
        html_parts = []
        is_list = False
        if any(element_node.get('ListNodes') for element_node in element_nodes):
            is_list = True
            html_parts.append('<ul>')

        for element_node in element_nodes:
            child_element = self._process_element_node(element_node, depth=depth + 1)
            if is_list:
                html_parts.extend(['<li>'] + child_element + ['</li>'])
            else:
                html_parts.extend(child_element)

        if is_list:
            html_parts.append('</ul>')
        return html_parts

    def _process_element_node(self, node, depth=0):
        """Recursively process an ElementChildNodes element.

        Look for:
        - ListNodes: indicates this is a list item
        - ContentChildNodes: contains RichEditTextUnicode with text and styling
        - ElementChildNodes: nested elements (for nested lists, etc.)
        """
        html_parts = []

        if not isinstance(node, dict):
            return html_parts

        # Skip title elements (these are handled separately)
        if node.get('IsTitleText') or node.get('IsTitleDate') or node.get('IsTitleTime'):
            return html_parts

        # Check if this is a list item (has ListNodes)
        # is_list_item = 'ListNodes' in node and node['ListNodes']

        # Process ContentChildNodes to extract text and styling
        content_parts = []
        if 'ContentChildNodes' in node:
            for content_child in node['ContentChildNodes']:
                if not isinstance(content_child, dict):
                    continue

                # Check for tables
                if 'RowCount' in content_child and 'ColumnCount' in content_child:
                    table_html = self._process_table(content_child)
                    if table_html:
                        content_parts.append(table_html)
                    continue

                # Check for images
                if 'PictureContainer' in content_child:
                    img_html = self._process_image(content_child['PictureContainer'])
                    if img_html:
                        content_parts.append(img_html)
                    continue

                # Check for embedded files
                if 'EmbeddedFileContainer' in content_child:
                    file_container = content_child['EmbeddedFileContainer']
                    filename = file_container.get('Filename', 'attachment')
                    content_parts.append(f'<div>[Attachment: {filename}]</div>')

                # Check for condensed JSON format (verbosity 0)
                # Format: { "type": "paragraph", "content": [{"text": "...", "attr": {...}}], "style": {...} }
                elif 'type' in content_child and 'content' in content_child:
                    # Extract text from content array
                    content_array = content_child.get('content', [])
                    if isinstance(content_array, list):
                        for text_obj in content_array:
                            if isinstance(text_obj, dict) and 'text' in text_obj:
                                text = text_obj['text']
                                if text and text.strip():
                                    # Apply formatting based on attr and style
                                    formatted_text = self._apply_condensed_formatting(text, text_obj, content_child)
                                    if formatted_text:
                                        content_parts.append(formatted_text)

                # Extract text from RichEditTextUnicode (higher verbosity levels)
                # Styling is from ParagraphStyle and TextRunFormatting at same level
                elif 'RichEditTextUnicode' in content_child:
                    text = content_child['RichEditTextUnicode']
                    if text and text.strip():
                        # Apply formatting based on ParagraphStyle and TextRunFormatting
                        formatted_text = self._apply_formatting(text, content_child)
                        if formatted_text:
                            content_parts.append(formatted_text)

                if 'ElementChildNodes' in content_child:
                    for element_child in content_child['ElementChildNodes']:
                        content_parts.extend(self._process_element_node(element_child, depth + 1))

        # If we have content, wrap it appropriately
        if content_parts:
            content = '\n'.join(content_parts)
            # if is_list_item:
                # Wrap in list item
                # html_parts.append(f'<li>{content}</li>')
            # else:
            html_parts.append(content)

        # Recursively process nested ElementChildNodes
        if 'ElementChildNodes' in node:
            html_parts.extend(self._process_element_list(node['ElementChildNodes'], depth=depth+1))
            # children = []
            # for child_element in node['ElementChildNodes']:
            #     children.extend(self._process_element_node(child_element, depth + 1))
            # if all(child.startswith('<li>') for child in children):
            #     children = ['<ul>'] + children + ['</ul>']
            # html_parts.extend(children)


    # If they're all <li> items, wrap with a <ul>
        # if all(part.startswith('<li>') for part in html_parts):
        #     html_parts = ['<ul>'] + html_parts + ['</ul>']
        return html_parts

    def _apply_condensed_formatting(self, text, text_obj, content_node):
        """Apply formatting to text from condensed JSON format.

        Args:
            text: The text string
            text_obj: Object containing 'text' and 'attr' fields
            content_node: Parent node containing 'type', 'content', and 'style'
        """
        # Clean up text - remove special whitespace characters
        text = text.replace('\u000b', ' ').replace('\u00a0', ' ').strip()

        if not text:
            return ''

        # Escape HTML special characters
        import html
        text = html.escape(text)

        # Get formatting attributes
        attr = text_obj.get('attr', {})
        style = content_node.get('style', {})

        # Apply text-level formatting (innermost tags)
        if attr.get('bold'):
            text = f'<b>{text}</b>'
        if attr.get('italic'):
            text = f'<i>{text}</i>'
        if attr.get('underline'):
            text = f'<u>{text}</u>'
        if attr.get('strikethrough'):
            text = f'<s>{text}</s>'

        # Apply paragraph-level styles (outermost tags)
        style_id = style.get('id', 'p')
        if style_id in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return f'<{style_id}>{text}</{style_id}>'
        elif style_id == 'code':
            return f'<code>{text}</code>'
        else:
            # Wrap in div for paragraph separation
            return f'<div>{text}</div>'

    def _apply_formatting(self, text, node):
        """Apply formatting to text based on node properties (for higher verbosity levels)."""
        # Clean up text - remove special whitespace characters
        text = text.replace('\u000b', ' ').replace('\u00a0', ' ').strip()

        if not text:
            return ''

        # Escape HTML special characters for text content only
        import html
        text = html.escape(text)

        # Get paragraph style
        para_style = node.get('ParagraphStyle', {})
        text_formatting = node.get('TextRunFormatting', [])

        # Apply paragraph style (headers, etc.)
        style_id = para_style.get('ParagraphStyleId', '')

        # Apply text formatting first (innermost tags)
        if text_formatting and len(text_formatting) > 0:
            fmt = text_formatting[0]
            if fmt and isinstance(fmt, dict):
                if fmt.get('Bold'):
                    text = f'<b>{text}</b>'
                if fmt.get('Italic'):
                    text = f'<i>{text}</i>'
                if fmt.get('Underline'):
                    text = f'<u>{text}</u>'
                if fmt.get('Strikethrough'):
                    text = f'<s>{text}</s>'

        # Then apply paragraph-level styles (outermost tags)
        if style_id in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return f'<{style_id}>{text}</{style_id}>'
        elif style_id == 'code':
            return f'<code>{text}</code>'
        else:
            # Wrap in div for paragraph separation
            return f'<div>{text}</div>'

    def _process_table(self, node):
        """Process a table node."""
        row_count = node.get('RowCount', 0)
        col_count = node.get('ColumnCount', 0)

        if row_count == 0 or col_count == 0:
            return None

        table_html = ['<table border="1">']

        # Process element children which contain table rows
        if 'ElementChildNodes' in node:
            for row in node['ElementChildNodes']:
                if isinstance(row, dict) and 'ElementChildNodes' in row:
                    table_html.append('<tr>')
                    for cell in row['ElementChildNodes']:
                        cell_content = self._process_table_cell(cell)
                        table_html.append(f'<td>{cell_content}</td>')
                    table_html.append('</tr>')

        table_html.append('</table>')
        return '\n'.join(table_html)

    def _process_table_cell(self, cell_node):
        """Process a table cell node."""
        cell_parts = []

        if not isinstance(cell_node, dict):
            return '&nbsp;'

        # Table cells contain ElementChildNodes with ContentChildNodes containing text
        if 'ElementChildNodes' in cell_node:
            for elem in cell_node['ElementChildNodes']:
                if isinstance(elem, dict) and 'ContentChildNodes' in elem:
                    for content in elem['ContentChildNodes']:
                        if isinstance(content, dict) and 'RichEditTextUnicode' in content:
                            text = content['RichEditTextUnicode']
                            if text and text.strip():
                                # Apply formatting but remove outer div wrapper for cells
                                formatted = self._apply_formatting(text, content)
                                # Strip the outer <div></div> tags for inline cell content
                                if formatted.startswith('<div>') and formatted.endswith('</div>'):
                                    formatted = formatted[5:-6]
                                cell_parts.append(formatted)

        return ' '.join(cell_parts) if cell_parts else '&nbsp;'

    def _process_image(self, picture_container):
        """Process an image and return placeholder HTML."""
        # Images will be added as resources, just return a placeholder
        filename = picture_container.get('Filename', 'image.png')
        # Generate hash for the resource
        import hashlib
        data = picture_container.get('Data', '')
        if data:
            hash_obj = hashlib.md5(data.encode() if isinstance(data, str) else data)
            hash_hex = hash_obj.hexdigest()
            return f'<en-media type="image/png" hash="{hash_hex}"/>'

        return ''

    def _extract_resources(self, page_data):
        """Extract all resources (images, attachments) from page data."""
        resources = []
        self._find_resources(page_data, resources)
        return resources

    def _find_resources(self, node, resources):
        """Recursively find all resources in the page data."""
        if isinstance(node, dict):
            # Check for picture container
            if 'PictureContainer' in node:
                resource_elem = self._create_image_resource(node['PictureContainer'], node)
                if resource_elem is not None:
                    resources.append(resource_elem)

            # Check for embedded file container
            if 'EmbeddedFileContainer' in node:
                resource_elem = self._create_file_resource(node['EmbeddedFileContainer'])
                if resource_elem is not None:
                    resources.append(resource_elem)

            # Recurse through child nodes
            for key in ['ContentChildNodes', 'ElementChildNodes', 'StructureElementChildNodes']:
                if key in node:
                    self._find_resources(node[key], resources)

        elif isinstance(node, list):
            for item in node:
                self._find_resources(item, resources)

    def _create_image_resource(self, picture_container, parent_node):
        """Create a resource element for an image."""
        resource = ET.Element('resource')

        # Get image data
        data = picture_container.get('Data', '')
        if not data:
            return None

        # Create data element with base64 encoding
        data_elem = ET.SubElement(resource, 'data')
        data_elem.set('encoding', 'base64')
        data_elem.text = data

        # Set MIME type
        mime_type = picture_container.get('MimeType', 'image/png')
        mime_elem = ET.SubElement(resource, 'mime')
        mime_elem.text = mime_type

        def to_pixels(size: float) -> int:
            return int(round(size * 48))  # Not sure where the 48 DPI comes from.

        width = parent_node.get("PictureWidth")
        height = parent_node.get("PictureHeight")
        if width and height:
            width_elem = ET.SubElement(resource, 'width')
            width_elem.text = str(to_pixels(width))
            height_elem = ET.SubElement(resource, 'height')
            height_elem.text = str(to_pixels(height))

        # Add filename if available
        filename = picture_container.get('Filename', '')
        if filename:
            attrs = ET.SubElement(resource, 'resource-attributes')
            filename_elem = ET.SubElement(attrs, 'file-name')
            filename_elem.text = filename

        return resource

    def _create_file_resource(self, file_container):
        """Create a resource element for an embedded file."""
        resource = ET.Element('resource')

        # Get file data
        data = file_container.get('Data', '')
        if not data:
            return None

        # Create data element with base64 encoding
        data_elem = ET.SubElement(resource, 'data')
        data_elem.set('encoding', 'base64')
        data_elem.text = data

        # Set MIME type
        mime_type = file_container.get('MimeType', 'application/octet-stream')
        mime_elem = ET.SubElement(resource, 'mime')
        mime_elem.text = mime_type

        # Add filename
        filename = file_container.get('Filename', 'attachment')
        attrs = ET.SubElement(resource, 'resource-attributes')
        filename_elem = ET.SubElement(attrs, 'file-name')
        filename_elem.text = filename

        # Mark as attachment
        attachment_elem = ET.SubElement(attrs, 'attachment')
        attachment_elem.text = 'true'

        return resource
