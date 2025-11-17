# Converting OneNote to ENEX Format

This guide explains how to convert Microsoft OneNote files to ENEX (Evernote Export) format for import into Apple Notes or other compatible applications.

## Quick Start

Convert a OneNote file to ENEX:

```bash
python 1note2enex.py mynotebook.one --output mynotes.enex
```

## Detailed Usage

### Basic Conversion

```bash
python 1note2enex.py <OneNote-file> --output <output.enex>
```

**Example:**
```bash
python 1note2enex.py "Meeting Notes.one" --output "meeting-notes.enex"
```

### With Additional Options

```bash
python 1note2enex.py mynotebook.one \
  --output output.enex \
  --verbose 1 \
  --log conversion.log
```

### List Available Revisions

Before converting, you can list all available revisions:

```bash
python 1note2enex.py mynotebook.one --list-revisions
```

## What Gets Converted

The ENEX converter preserves the following from your OneNote files:

### Content
- ✅ Page titles
- ✅ Text content
- ✅ Tables
- ✅ Images (embedded as base64)
- ✅ File attachments (embedded as base64)

### Formatting
- ✅ Bold, italic, underline, strikethrough
- ✅ Headers (h1-h6)
- ✅ Paragraph styles
- ✅ Code blocks
- ✅ Lists and indentation

### Metadata
- ✅ Creation timestamps
- ✅ Modification timestamps
- ✅ Author information

## Importing into Apple Notes

1. Convert your OneNote file to ENEX:
   ```bash
   python 1note2enex.py mynotebook.one --output mynotes.enex
   ```

2. Open Apple Notes

3. From the menu bar, select: **File → Import to Notes...**

4. Select your `.enex` file

5. Click **Import**

Your OneNote pages will now appear as individual notes in Apple Notes!

## Importing into Evernote

1. Convert your OneNote file to ENEX:
   ```bash
   python 1note2enex.py mynotebook.one --output mynotes.enex
   ```

2. Open Evernote

3. From the menu bar, select: **File → Import Notes...**

4. Select your `.enex` file

5. Choose the destination notebook

6. Click **Import**

## Command Line Options

### Required Options

- `<OneNote-file>`: Path to your `.one` or `.onetoc2` file
- `--output <filename>` or `-O <filename>`: Output ENEX file path

### Optional Options

- `--log <logfile>` or `-L <logfile>`: Write detailed conversion log
- `--verbose <level>` or `-v <level>`: Verbosity level (0-5, default: 0)
- `--include-oids` or `-o`: Include object IDs (for debugging)
- `--list-revisions` or `-l`: List all available revisions

## Examples

### Convert a Single Section

```bash
python 1note2enex.py "Work Notes.one" --output "work-notes.enex"
```

### Convert with Logging

```bash
python 1note2enex.py notebook.one \
  --output notes.enex \
  --log conversion.log \
  --verbose 1
```

### List Revisions Before Converting

```bash
# First, list available revisions
python 1note2enex.py notebook.one --list-revisions

# Then convert the current version
python 1note2enex.py notebook.one --output current.enex
```

## Troubleshooting

### Images Not Appearing

Make sure auto-sync is enabled in OneNote:
1. Go to OneNote Settings
2. Select **General → Sync → Auto Sync Attachments**
3. Re-save your notebook and try converting again

### Missing Content

Try increasing the verbosity level:
```bash
python 1note2enex.py mynotebook.one --output notes.enex --verbose 2
```

### Large Files

For very large OneNote files, the conversion may take several minutes. Use the `--log` option to monitor progress:
```bash
python 1note2enex.py large-notebook.one \
  --output output.enex \
  --log progress.log
```

## Technical Details

### ENML Format

The converter generates valid ENML (Evernote Markup Language) content, which is a subset of HTML with specific restrictions:

- All content is wrapped in `<en-note>` tags
- Images and attachments are embedded as base64-encoded `<resource>` elements
- Only a limited set of HTML tags are supported
- All resources include MD5 hashes for integrity verification

### Resource Handling

- **Images**: Converted to base64 and embedded with MIME type (PNG, JPEG, etc.)
- **Attachments**: Embedded as base64 with proper MIME types (PDF, etc.)
- **Links**: Preserved where possible

### Timestamp Format

Dates are converted to ISO 8601 format as required by ENEX:
```
yyyymmddThhmmssZ
```

For example: `20240115T143022Z` represents January 15, 2024 at 2:30:22 PM UTC.

## Known Limitations

- OneNote's free-form canvas layout is converted to linear note format
- Some advanced OneNote features (audio notes, embedded Excel sheets) may not convert perfectly
- Page backgrounds and themes are not preserved
- Drawing/ink annotations are converted to images where possible

## Support

For issues or questions:
- Check the conversion log file for detailed error messages
- Ensure your OneNote file is not corrupted
- Verify you have the latest version of Python (3.9+)
