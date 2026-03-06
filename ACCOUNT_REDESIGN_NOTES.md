# Account Page Redesign - Implementation Notes

## Changes to Make:

### 1. Add i18n attributes to account.html
Replace all Vietnamese text with data-i18n attributes:
- `<h1>🎯 Quản lý tài khoản</h1>` → `<h1 data-i18n="account_title">🎯 Quản lý tài khoản</h1>`
- All labels, buttons, text content

### 2. Merge extended translations into translations.js
Copy content from translations_extended.js into the main translations.js file

### 3. Update account.html structure for better responsive design
- Use CSS Grid with better breakpoints
- Add smooth transitions
- Improve card shadows and borders
- Add hover effects
- Better mobile layout

### 4. Key sections to update with i18n:
- Page title and subtitle
- Profile section (username, email, member since)
- Premium status section
- Downloads section  
- Benefits list
- Payment section
- Buttons (home, logout, pay now)
- Success modal

### 5. CSS improvements:
- Add gradient backgrounds
- Smooth animations
- Better spacing
- Modern card design
- Responsive grid layout
- Hover effects

## Implementation Priority:
1. First: Merge translations (DONE - file created)
2. Second: Update account.html with i18n attributes
3. Third: Improve CSS styling
4. Fourth: Test all 3 languages

## Files to modify:
- static/js/translations.js (merge extended translations)
- templates/auth/account.html (add i18n, improve layout)
- static/css/auth.css (optional - improve styling)
