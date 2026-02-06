# VALLORYS Design System - Airbnb Warm Style

## Preview Component

```html
<!-- DESIGN SYSTEM REFERENCE -->
<div class="font-sans bg-white min-h-screen">

  <!-- Sidebar -->
  <aside class="w-64 bg-white border-r border-gray-100 p-6 fixed h-full">
    <div class="text-2xl font-bold text-gray-900 mb-8 tracking-tight">VALLORYS</div>
    <nav class="space-y-1">
      <a href="#" class="flex items-center gap-3 px-4 py-3 bg-rose-50 text-rose-600 rounded-xl font-medium">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
        </svg>
        Dashboard
      </a>
      <a href="#" class="flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
        </svg>
        Estimations
      </a>
      <a href="#" class="flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
        </svg>
        Coach
      </a>
      <a href="#" class="flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
        </svg>
        Analytics
      </a>
    </nav>
  </aside>

  <!-- Main Content -->
  <main class="ml-64 p-8 bg-gray-50/50 min-h-screen">

    <!-- Header -->
    <header class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 tracking-tight">Bonjour, Marie 👋</h1>
      <p class="text-gray-500 mt-1">Voici votre activité du jour</p>
    </header>

    <!-- Stats Cards -->
    <div class="grid grid-cols-4 gap-6 mb-8">
      <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <div class="flex items-center justify-between mb-4">
          <span class="text-gray-500 text-sm font-medium">Estimations</span>
          <span class="w-10 h-10 bg-rose-50 rounded-xl flex items-center justify-center">
            <svg class="w-5 h-5 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
            </svg>
          </span>
        </div>
        <p class="text-3xl font-bold text-gray-900">127</p>
        <p class="text-sm text-emerald-600 mt-1 flex items-center gap-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
          </svg>
          +12% ce mois
        </p>
      </div>

      <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <div class="flex items-center justify-between mb-4">
          <span class="text-gray-500 text-sm font-medium">Conversion</span>
          <span class="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center">
            <svg class="w-5 h-5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
            </svg>
          </span>
        </div>
        <p class="text-3xl font-bold text-gray-900">47%</p>
        <p class="text-sm text-emerald-600 mt-1 flex items-center gap-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
          </svg>
          +3 points
        </p>
      </div>

      <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <div class="flex items-center justify-between mb-4">
          <span class="text-gray-500 text-sm font-medium">Précision</span>
          <span class="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center">
            <svg class="w-5 h-5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </span>
        </div>
        <p class="text-3xl font-bold text-gray-900">96.2%</p>
        <p class="text-sm text-gray-500 mt-1">MAPE: 4.2%</p>
      </div>

      <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <div class="flex items-center justify-between mb-4">
          <span class="text-gray-500 text-sm font-medium">RDV Today</span>
          <span class="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
            <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            </svg>
          </span>
        </div>
        <p class="text-3xl font-bold text-gray-900">3</p>
        <p class="text-sm text-gray-500 mt-1">Prochain: 14h30</p>
      </div>
    </div>

    <!-- Estimation Card -->
    <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-6">
      <div class="flex items-start justify-between mb-6">
        <div>
          <div class="flex items-center gap-3 mb-2">
            <h2 class="text-xl font-bold text-gray-900">Appartement 85m²</h2>
            <span class="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-sm font-medium">Confiance élevée</span>
          </div>
          <p class="text-gray-500">Lyon 1er • 4 pièces • 3ème étage • DPE D</p>
        </div>
        <button class="px-4 py-2 bg-gray-900 text-white rounded-xl font-medium hover:bg-gray-800 transition-colors">
          Voir le rapport
        </button>
      </div>

      <div class="grid grid-cols-3 gap-8">
        <div>
          <p class="text-sm text-gray-500 mb-1">Prix recommandé</p>
          <p class="text-4xl font-bold text-gray-900">365 000 €</p>
          <p class="text-sm text-gray-500 mt-2">Fourchette: 339 000 € - 390 000 €</p>
        </div>
        <div>
          <p class="text-sm text-gray-500 mb-1">Prix au m²</p>
          <p class="text-2xl font-bold text-gray-900">4 294 €/m²</p>
          <p class="text-sm text-emerald-600 mt-2">+1% vs médiane secteur</p>
        </div>
        <div>
          <p class="text-sm text-gray-500 mb-1">Score de confiance</p>
          <div class="flex items-center gap-3">
            <div class="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full w-[84%] bg-gradient-to-r from-rose-400 to-amber-400 rounded-full"></div>
            </div>
            <span class="text-lg font-bold text-gray-900">84%</span>
          </div>
          <p class="text-sm text-gray-500 mt-2">Marge: ±7%</p>
        </div>
      </div>
    </div>

    <!-- Adjustments -->
    <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <h3 class="font-bold text-gray-900 mb-4">Ajustements appliqués</h3>
      <div class="space-y-3">
        <div class="flex items-center justify-between py-3 border-b border-gray-50">
          <div class="flex items-center gap-3">
            <span class="w-8 h-8 bg-red-50 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"/>
              </svg>
            </span>
            <span class="text-gray-700">DPE D : légère décote énergétique</span>
          </div>
          <span class="text-red-600 font-semibold">-3%</span>
        </div>
        <div class="flex items-center justify-between py-3 border-b border-gray-50">
          <div class="flex items-center gap-3">
            <span class="w-8 h-8 bg-emerald-50 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
              </svg>
            </span>
            <span class="text-gray-700">3ème étage avec ascenseur</span>
          </div>
          <span class="text-emerald-600 font-semibold">+2%</span>
        </div>
        <div class="flex items-center justify-between py-3">
          <div class="flex items-center gap-3">
            <span class="w-8 h-8 bg-emerald-50 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
              </svg>
            </span>
            <span class="text-gray-700">Secteur recherché avec forte liquidité</span>
          </div>
          <span class="text-emerald-600 font-semibold">+2%</span>
        </div>
      </div>
    </div>

  </main>
</div>
```

## Design Tokens

### Colors
```css
/* Primary - Rose (Airbnb-inspired) */
--color-primary-50: #fff1f2;
--color-primary-100: #ffe4e6;
--color-primary-200: #fecdd3;
--color-primary-300: #fda4af;
--color-primary-400: #fb7185;
--color-primary-500: #f43f5e;  /* Main accent */
--color-primary-600: #e11d48;
--color-primary-700: #be123c;

/* Secondary - Amber (Warm touch) */
--color-secondary-50: #fffbeb;
--color-secondary-100: #fef3c7;
--color-secondary-400: #fbbf24;
--color-secondary-500: #f59e0b;
--color-secondary-600: #d97706;

/* Neutrals */
--color-gray-50: #f9fafb;
--color-gray-100: #f3f4f6;
--color-gray-200: #e5e7eb;
--color-gray-300: #d1d5db;
--color-gray-400: #9ca3af;
--color-gray-500: #6b7280;
--color-gray-600: #4b5563;
--color-gray-700: #374151;
--color-gray-800: #1f2937;
--color-gray-900: #111827;

/* Semantic */
--color-success: #10b981;
--color-warning: #f59e0b;
--color-error: #ef4444;
--color-info: #3b82f6;
```

### Typography
```css
/* Font Family - Clean, rounded, modern */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;

/* Line Heights */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.625;
```

### Spacing & Radius
```css
/* Border Radius - Generous, friendly */
--radius-sm: 0.5rem;   /* 8px */
--radius-md: 0.75rem;  /* 12px */
--radius-lg: 1rem;     /* 16px */
--radius-xl: 1.5rem;   /* 24px - Cards */
--radius-2xl: 2rem;    /* 32px */
--radius-full: 9999px;

/* Shadows - Subtle, soft */
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.05), 0 4px 6px -4px rgb(0 0 0 / 0.05);
```

### Component Patterns

#### Buttons
```html
<!-- Primary -->
<button class="px-6 py-3 bg-gray-900 text-white rounded-xl font-medium hover:bg-gray-800 transition-colors">
  Action
</button>

<!-- Secondary -->
<button class="px-6 py-3 bg-white text-gray-900 border border-gray-200 rounded-xl font-medium hover:bg-gray-50 transition-colors">
  Secondary
</button>

<!-- Accent -->
<button class="px-6 py-3 bg-rose-500 text-white rounded-xl font-medium hover:bg-rose-600 transition-colors">
  Accent
</button>
```

#### Cards
```html
<div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
  <!-- Content -->
</div>
```

#### Badges
```html
<span class="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-sm font-medium">Success</span>
<span class="px-3 py-1 bg-rose-50 text-rose-700 rounded-full text-sm font-medium">Alert</span>
<span class="px-3 py-1 bg-amber-50 text-amber-700 rounded-full text-sm font-medium">Warning</span>
```

#### Input Fields
```html
<input type="text"
  class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-rose-500 focus:border-transparent outline-none transition-all"
  placeholder="Rechercher...">
```

### Icons
Use Heroicons (outline style, stroke-width: 1.5) for consistency with Airbnb aesthetic.

### Animation
```css
/* Transitions */
--transition-fast: 150ms ease;
--transition-base: 200ms ease;
--transition-slow: 300ms ease;

/* Hover effects */
.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}
```
