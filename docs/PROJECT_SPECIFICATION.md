# Page Society Template Generator

## Master Project Specification (Version 1.0)

---

# 1. Project Name

**Page Society Template Generator (PSTG)**

---

# 2. Project Vision

Page Society Template Generator is a professional desktop application for generating accurate, print-ready book cover templates.

The software is intended for authors, publishers, designers, and print professionals who need high-quality publishing templates for multiple paper standards and printer profiles.

The application must work completely offline after installation.

This specification defines the project's architecture, scope, modules, and development rules.

---

# 3. Project Scope

The software generates professional book cover templates.

The software does **not** include:

* Interior page creation
* Mockup generation
* Logo design
* Brand management
* Image editing
* Desktop publishing
* Book editing

These features are intentionally outside the scope of Version 1.0.

---

# 4. Primary Goal

Generate accurate publishing templates from user inputs.

User Input →

Template Engine →

Live Preview →

Export

---

# 5. Target Users

* Amazon KDP publishers
* IngramSpark publishers
* Self-publishers
* Graphic designers
* Printing companies
* Publishing houses

---

# 6. Technology Stack

Language:

* Python 3.13+

GUI:

* PySide6 (Qt)

Graphics:

* SVG
* PDF

Image Export:

* Pillow

Configuration:

* JSON

Testing:

* pytest

Version Control:

* Git

Documentation:

* Markdown

Operating Systems:

* Windows
* Linux
* macOS

---

# 7. Internal Measurement Standard

All internal calculations must use **millimetres (mm)**.

Conversions to inches are for display and export only.

Resolution defaults to **300 PPI** for raster exports.

---

# 8. Supported Paper Standards

Version 1.0 shall support:

* ISO A Series
* ISO B Series
* ISO C Series
* US Letter
* US Legal
* Executive
* Composition
* Square formats
* Signature/Folio formats
* Custom paper sizes

Each paper size is represented as structured data.

No paper size shall be hardcoded into calculation logic.

---

# 9. Supported Book Types

* Paperback
* Hardcover
* Perfect Bound
* Case Bound
* Saddle Stitch
* Spiral Bound
* Wire-O

The architecture must allow additional binding types.

---

# 10. Printer Profiles

Version 1.0 supports:

* Page Society Standard
* Amazon KDP
* IngramSpark
* Local Printer
* Offset Printer
* Custom Printer

Each printer profile defines its own:

* Bleed
* Safe area
* Spine calculation
* Barcode zone
* Export rules

The calculation engine must never hardcode printer-specific values.

---

# 11. User Inputs

The application shall accept:

* Printer profile
* Paper standard
* Book size
* Custom dimensions
* Page count
* Binding type
* Bleed
* Safe area
* Spine mode (automatic/manual)
* Barcode visibility
* Measurement unit (mm/inches)

---

# 12. Outputs

The application shall export:

* SVG
* PDF
* PNG
* JPG

Future export formats must be pluggable.

---

# 13. Live Preview

The application shall display a real-time preview containing:

* Back cover
* Spine
* Front cover
* Bleed
* Trim
* Safe area
* Barcode zone
* Guides

The preview updates automatically whenever input values change.

---

# 14. Page Society Standard

Default values:

* Bleed: 3 mm
* Safe Area: 5 mm
* Resolution: 300 PPI

Printer profiles may override these defaults.

---

# 15. Folder Structure

```
PageSocietyTemplateGenerator/

app/
    ui/
    core/
    generators/
    exporters/
    printer_profiles/
    standards/
    models/
    utils/
    resources/

config/
docs/
exports/
tests/

main.py
README.md
requirements.txt
```

---

# 16. Core Modules

## UI

Responsible only for user interaction.

Contains:

* Main window
* Navigation
* Toolbars
* Property panels
* Status bar
* Live preview integration

Contains no business logic.

---

## Standards Module

Stores paper standards.

Provides paper dimensions.

Supports custom standards.

---

## Printer Profiles Module

Loads printer profile data.

Provides:

* Bleed
* Safe area
* Spine rules
* Barcode rules

---

## Generator Module

Responsible for building templates.

Generates:

* Front cover
* Back cover
* Spine
* Guides
* Bleed
* Safe area
* Barcode zone

---

## Export Module

Exports templates to:

* SVG
* PDF
* PNG
* JPG

---

## Models

Defines application data structures.

Examples:

* PaperSize
* PrinterProfile
* BookSpecification
* TemplateLayout
* ExportOptions

---

## Utilities

Shared reusable functionality such as:

* Unit conversion
* Validation
* Geometry helpers
* File helpers
* Logging helpers

---

# 17. UI Layout

The interface consists of:

* Toolbar
* Left navigation panel
* Central live preview
* Right properties panel
* Status bar

The layout should remain clean, scalable, and suitable for future enhancement.

---

# 18. Design Principles

* Modular architecture
* Data-driven design
* No duplicated code
* No hardcoded printer values
* No business logic in UI classes
* Type hints throughout
* PEP 8 compliance
* Public docstrings
* Robust error handling
* Logging instead of print()
* Maintainability over cleverness

---

# 19. Development Workflow

Build exactly one milestone at a time.

After each milestone:

1. Ensure the application runs successfully.
2. Summarize the implementation.
3. List all created and modified files.
4. Explain architectural decisions.
5. Wait for approval before continuing.

Never begin the next milestone automatically.

---

# 20. Milestones

1. Project Skeleton
2. Application Shell
3. Paper Standards Engine
4. Printer Profile Engine
5. Template Calculation Engine
6. Live Preview
7. SVG Export
8. PDF Export
9. PNG/JPG Export
10. Settings & Preferences
11. Testing
12. Packaging & Distribution

---

# 21. Definition of Done

A milestone is complete only when:

* The project builds successfully.
* The application launches without errors.
* Imports are clean.
* Type hints are complete.
* Public APIs are documented.
* Error handling is implemented.
* Logging is in place.
* No placeholder implementations remain for that milestone.

---

# 22. Long-Term Objective

The goal of Page Society Template Generator Version 1.0 is to provide a reliable, professional, and extensible desktop application that generates accurate, print-ready book cover templates for multiple publishing workflows while maintaining a clean architecture that supports future growth without major redesign.
