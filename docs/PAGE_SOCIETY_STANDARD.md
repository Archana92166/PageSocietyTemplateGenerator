# Page Society Publishing Standard

## Master Template Philosophy

Every supported book size has exactly one master template.

The master template remains fixed throughout the life of the project.

Only the spine width changes.

Everything else remains constant.

--------------------------------------------------------

Fixed Components

✓ Trim Size
✓ Bleed
✓ Safe Area
✓ Total Height
✓ Front Cover
✓ Back Cover
✓ Barcode Reserved Area
✓ Guide Positions
✓ Layer Structure
✓ Artwork Regions

--------------------------------------------------------

Dynamic Component

✓ Spine Width

The spine width is calculated automatically using:

- Printer Profile
- Binding Type
- Paper Type
- Page Count

The user never enters the spine width manually.

--------------------------------------------------------

Flat Width Formula

Flat Width

=

(2 × Trim Width)
+
Spine Width
+
(2 × Bleed)

--------------------------------------------------------

Total Height Formula

Total Height

=

Trim Height
+
(2 × Bleed)

--------------------------------------------------------

Default Values

Bleed
3 mm

Safe Area
5 mm

--------------------------------------------------------

Barcode Categories

Large
40 × 30 mm

Medium
35 × 25 mm

Small
30 × 20 mm