```yaml
type: NotebookSection
pages:
  PageID:  # {{GUID}}
    ContentChildNodes: # Usually just a single child in the array
      - PageMarginOriginX: <float>
        PageMarginOriginY: <float>
        StructureElementChildNodes:
          # Overall layout of the page. Usually just a single child in the array
          - OffsetFromParentHoriz: <float>
            OffsetFromParentVert: <floag>
            LayoutAlignmentSelf: null
            LayoutAlignmentInParent:
              HorizontalAlignment: StartOfLine # e.g.
              fHorizMargin: StartOfLine
              VerticalAlignment: Top
              fVertMargin: Top
            LastModifiedTime: <unix epooc seconds>  # This is probably the most reliable timestamp to use
            ElementChildNodes:
              - OutlineElementChildLevel: 1
                ElementChildNodes:
                  - IsTitleText: true | false
                    LastModifiedTime: <unix seconds>
                    ContentChildNodes:
                      - LastModifiedTime: <unix seconds>
                        ParagraphStyle:
                          Font:
                          FontSize:
                          FontColor:
                          etc:
                        IsTitleText: true
                        RichEditTextUnicode: "Page Title Here"
              - IsTitleDate: true
                IsReadOnly: true
                Deletable: true
                ElementChildNodes:
                  - ContentChildNodes: # Formatted Page Date
                      - ParagraphStyle:
                          Font:
                          FontSize:
                          FontColor:
                          etc:
                        IsBoilerText: true
                        IsTitleDate: true
                        IsReadOnly: true
                        RichTextLangID: 1033 # Determines timezone?
                        RichEditTextUnicode: Thursday, April 10, 2014
                  - ContentChildNodes: # Formatted Page Time
                      - ParagraphStyle:
                          etc:
                        RichTextLangID: 1033 # Determines timezone?
                        RichEditTextUnicode: 11:38 AM
        PredefinedParagraphStyles:
          # Defines the global styles used in the page content.
          - Font: Calibri
            FontSize: 22
            FontColor: null
            ParagraphSpaceBefore: 0.0
            ParagraphSpaceAfter: 0.0
            ParagraphStyleId: p | h2 | h3 | etc.
            Property_C0034DA: 2  # ??
          - etc:
        ElementChildNodes:
          # Note content.  Usually this is a single node, but if there are multiple text areas floating
          # around, there might be multiple, with directions for where on the page the box lives.
          - OutlineElementChildLevel: 1
            OffsetFromParentHoriz: 1.0
            OffsetFromParentVert: 2.5
            LayoutMaxWidth: 13.0
            LayoutAlignmentSelf:
              HorizontalAlignment: Left
              fHorizMargin: StartOfLine
              VerticalAlignment: Bottom
              fVertMargin: Bottom
            RgOutlineIndentDistance: [ float, float, float, float ]
            LastModifiedTime: <unix epoch seconds>
            ElementChildNodes:
              ContentChildNodes:
                - RowCount: 1
                  ColumnCount: 1
                  TableBordersVisible: false
                  TableColumnWidths: [ <float> ]
                  ElementChildNodes:
                    - ElementChildNodes:
                        - ParagraphStyle:
                            Font:
                            FontSize:
                            FontColor:
                              ParagraphStyleId: p | h2 | h3 | etc.
                            etc:
                          RichEditTextUnicode: "Some portion of page content."

    VersionHistoryGraphSpaceContextNodes:
    MetaDataObjectsAboveGraphSpace:
    PageLevel: 1
    CachedTitleString: "Page Title"
    NotebookManagementEntityGuid: "{GUID}"
    HasVersionPages: true | false
    TopologyCreationTimestamp: <LDAP/Win32 FILENAME (nanos since jan 1, 1601 UTC)
    SchemaRevisionInOrderToRead: <int>
    SchemaRevisionInOrderToWrite: <int>
    LastModifiedTimestamp: LDAP/Win32 FILENAME time
    AuthorMostRecent:
      Author: My Name
      AuthorInitials: MN

```
