# Design System Specification: The Precision Ledger

## 1. Overview & Creative North Star
**Creative North Star: "The Architectural Whisper"**

This design system rejects the "noisy" density common in enterprise fintech. Instead, it adopts a high-end editorial approach that treats financial data with the reverence of a museum gallery. We move beyond the "template" look by utilizing **Intentional Asymmetry** and **Tonal Depth**. 

The system is built on a foundation of "Quiet Authority." By using expansive white space (`spacing-16` or `spacing-20` between major sections) and a sophisticated hierarchy of neutral surfaces, we guide the user’s eye not through loud borders, but through logical, layered light. Every element should feel like it was placed by a curator—precise, intentional, and expensive.

---

## 2. Colors & Surface Philosophy
The palette is rooted in slate and stone neutrals, punctuated by "Risk Tones" that serve as functional beacons rather than decorative elements.

### The "No-Line" Rule
**Strict Mandate:** Designers are prohibited from using 1px solid borders for sectioning or layout containment. Structural boundaries must be defined exclusively through:
*   **Background Shifts:** e.g., A `surface-container-low` section resting on a `surface` background.
*   **Tonal Transitions:** Using the `surface-container` tiers to create logical groupings.

### Surface Hierarchy & Nesting
Treat the UI as a physical stack of premium cardstock.
*   **Base Layer:** `surface` (#f7f9fb)
*   **Sectional Underlay:** `surface-container-low` (#f0f4f7)
*   **Primary Interactive Surface:** `surface-container-lowest` (#ffffff)
*   **Elevated Overlays:** `surface-bright` (#f7f9fb) with glassmorphism.

### The "Glass & Gradient" Rule
To elevate the "out-of-the-box" feel, use **Glassmorphism** for floating elements (Modals, Hover Tooltips). Apply semi-transparent `surface` colors with a `backdrop-blur-xl` effect.
*   **Signature Texture:** Main CTAs or Hero Cards should utilize a subtle linear gradient: `primary` (#565e74) to `primary-dim` (#4a5268) at a 135-degree angle. This adds "soul" to the flat fintech environment.

---

## 3. Typography
We utilize a dual-typeface system to balance editorial elegance with high-density data readability.

*   **Display & Headlines (Manrope):** Chosen for its geometric precision and modern "tech-forward" terminals. Headlines should be tight-tracked (-0.02em) to feel authoritative.
*   **Body & Labels (Inter):** Chosen for its unparalleled legibility in small-scale financial tables.

**The Hierarchy of Intent:**
*   **Display-LG (3.5rem):** Reserved for portfolio totals or primary brand statements.
*   **Label-SM (0.6875rem, All Caps, Spacing 0.05em):** Used for metadata and table headers. This "muted" treatment (`on-surface-variant`) ensures that the data itself remains the hero.

---

## 4. Elevation & Depth
Depth is a functional tool, not a stylistic flourish. We convey hierarchy through **Tonal Layering** rather than traditional structural shadows.

*   **The Layering Principle:** Place a `surface-container-lowest` card on a `surface-container-low` section. The contrast in hex values provides all the "lift" required.
*   **Ambient Shadows:** If an element must float (e.g., a dropdown), use a shadow tinted with the `on-surface` color: `box-shadow: 0 20px 40px -12px rgba(42, 52, 57, 0.06)`. This mimics soft, natural gallery lighting.
*   **The "Ghost Border" Fallback:** If a container lacks sufficient contrast against its neighbor, use a `1px` border of `outline-variant` at **15% opacity**. Never use 100% opaque borders.

---

## 5. Components

### Cards & Containers
*   **The Rule of Flow:** Forbid the use of divider lines. Separate content blocks using `spacing-6` or `spacing-8`. 
*   **Rounding:** Use `rounded-md` (1.5rem) for primary dashboard cards and `rounded-full` for all action chips and tags.

### Risk Indicators (Pill-Shaped)
These must be high-contrast and utilize the "Risk Palette" for instant cognitive processing:
*   **Grade A (Strong):** `bg-tertiary-fixed` / `on-tertiary-fixed`.
*   **Grade C (Watch):** `bg-amber-50` / `text-amber-600`.
*   **Grade E (Risk):** `bg-error-container` / `on-error-container`.

### Action Buttons
*   **Primary:** `primary` (#565e74) background, `on-primary` text. No border. Soft `lg` (2rem) corner radius.
*   **Secondary:** `surface-container-high` background. Text in `on-surface`. This creates a "recessed" look that doesn't compete for attention.

### Pulse Loading States
Avoid generic spinners. Use a **Tonal Pulse** on skeleton screens. Animate the `surface-container-highest` token's opacity from 40% to 100% to mimic a breathing rhythm.

### Input Fields
*   **Default State:** `surface-container-lowest` background with a "Ghost Border" (10% `outline`).
*   **Focus State:** Shift background to `surface-bright` and increase border opacity to 40% using the `primary` color.

---

## 6. Do’s and Don’ts

### Do:
*   **Embrace Asymmetry:** Align the main header to the left, but place secondary stats in an offset, right-aligned grid to create visual interest.
*   **Use Generous Leading:** Set body text line height to 1.6 for readability in dense financial reports.
*   **Nesting Surfaces:** Use `surface-container-lowest` for the most interactive elements to make them feel "closest" to the user.

### Don’t:
*   **Don't use 100% Black:** Always use `on-surface` (#2a3439) for text to maintain a premium, softer look.
*   **Don't use Dividers:** Never use a horizontal rule `<hr>` to separate list items. Use vertical spacing.
*   **Don't Over-Shadow:** If more than two elements on a screen have shadows, the layout is too busy. Revert to Tonal Layering.
*   **No Sharp Corners:** Except for the `none` token for absolute backgrounds, every interactive element must have at least a `sm` (0.5rem) radius to feel approachable and modern.