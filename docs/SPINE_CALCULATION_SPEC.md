# Spine Calculation Specification

Purpose

Convert page count into spine width.

Inputs

Printer Profile

Binding

Paper Type

Page Count

Output

Spine Width (mm)

--------------------------------------------------------

The engine supports multiple strategies.

Strategy 1

Formula

Example

Spine Width

=

Page Count × Paper Thickness

--------------------------------------------------------

Strategy 2

Lookup Table

Example

24 Pages

↓

1.8 mm

48 Pages

↓

3.2 mm

96 Pages

↓

6.4 mm

--------------------------------------------------------

Every printer profile selects its own strategy.

Amazon KDP

↓

Lookup or Formula

IngramSpark

↓

Lookup or Formula

Local Printer

↓

Custom Formula

--------------------------------------------------------

The Master Template Engine never performs spine calculations.

It only consumes the calculated spine width.