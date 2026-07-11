# Task 2 Report: Shadcn Primitives + a11y Sweep

## Status: DONE

## Commits
- `121c91b` feat(ui): Button + IconButton primitives with cva variants
- `8934693` feat(ui): Input + Textarea + Card primitives with design tokens
- `fba3217` feat(ui): Dialog + Sheet + Popover + Tooltip via Radix primitives
- `b7ffcad` feat(ui): Skeleton + Tabs + Badge + Separator + Accordion
- `c79343f` feat(ui): ToggleGroup + RadioGroup + Switch + Combobox
- `a9c5eaa` feat(ui): Command primitives wrapping cmdk
- `26c8ae0` feat(ui): Toast (sonner) wired to layout + a11y sweep tests passing

## Tests
7 tests passing across button.test.tsx (3 tests) + accessibility.test.tsx (4 tests)

## Concerns
- All primitives written by hand (not via Shadcn CLI) to avoid Tailwind 4 incompatibility — this is the recommended approach per brief.
- CSS variable references use `var(--token)` syntax in Tailwind arbitrary value brackets (e.g. `bg-[var(--primary)]`) rather than Tailwind utility class names like `bg-primary`. This is because `@theme inline` in Tailwind 4 registers colors under `--color-*` namespace but the `var()` bracket syntax works reliably without needing to verify exact registration names.
- `duration-[120ms]` etc. uses arbitrary value syntax since `duration-120` is not a standard Tailwind utility (Tailwind ships `duration-100`, `duration-200`, etc.). The design-token variable `--duration-fast: 120ms` exists in globals.css but is not yet registered in `@theme inline` as a duration scale — reviewer may want to add `--animate-duration-fast: var(--duration-fast)` mappings if strict utility classes are preferred.
- Textarea uses `field-sizing-content` for CSS-native auto-grow (no JS resize needed; supported in all modern browsers used by A-Level students; safe to ship).
- Accordion animation classes (`animate-accordion-up/down`) are referenced in AccordionContent but no corresponding keyframes are defined in globals.css — these are no-ops until keyframes are added. Accordion is structurally correct and a11y-compliant; only the open/close animation is missing.
- jest-axe (v10.0.0) and @types/jest-axe (v3.5.9) added to devDependencies.

## Fix commit(s)

### Commits
- `c107e95` Fix Task 2 review findings: I1 focus ring, I2 tooltip shadow, I3 sheet surface
- `df70279` Adopt token utilities: ease-standard, rounded-{input,card,dialog}, duration-{fast,base,slow} + register duration aliases in globals.css

### Findings addressed
- **I1** — Removed `focus-visible:outline-none` from every primitive: button, input, textarea, dialog (DialogClose), sheet (SheetClose), tabs (TabsTrigger + TabsContent), switch, accordion (AccordionTrigger), toggle-group (ToggleGroupItem), radio-group (RadioGroupItem). Global `*:focus-visible` rule in globals.css now applies unobstructed.
- **I2** — Removed `shadow-lg` from `TooltipContent`. Tooltip no longer violates the shadow-allowed list (Dialog, Sheet, Popover only).
- **I3** — `SheetContent` now uses a `surfaceClasses` lookup map (same pattern as `Card`) and respects the `data-surface` prop. Default surface changed from `"2"` to `"3"` per design spec (sheets ARE Surface 3).
- **m5** — Replaced every `ease-[cubic-bezier(.22,.61,.36,1)]` with `ease-standard` across all ui primitives (button, input, textarea, dialog, sheet, tabs, switch, accordion, toggle-group, radio-group, badge).
- **m6** — Replaced `rounded-[8px]` → `rounded-input`, `rounded-[10px]` → `rounded-card`, `rounded-[14px]` → `rounded-dialog` across all ui primitives, card, and skeleton.
- **m2** — Added `--transition-duration-fast: 120ms`, `--transition-duration-base: 220ms`, `--transition-duration-slow: 320ms` to `@theme inline` in `globals.css` so Tailwind 4 generates `duration-fast/base/slow` utilities. Replaced all `duration-[120ms]` → `duration-fast`, `duration-[220ms]` → `duration-base`, `duration-[320ms]` → `duration-slow` across all ui primitives.

### Test run
```
cd web && npx vitest run src/components/ui/
```
Result: **2 test files, 7 tests — all passed** (button.test.tsx 3 + accessibility.test.tsx 4)

### Focus ring verification
```
grep -rn "focus-visible:outline-none" web/src/components/ui/
```
Result: **zero matches**
