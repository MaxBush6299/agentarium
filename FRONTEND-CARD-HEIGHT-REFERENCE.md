# Frontend Agent Card Height Adjustment - Reference Guide

**Date:** October 23, 2025  
**Status:** Todo Item Added  
**Location:** `/frontend/src/components/agents/AgentCard.tsx`

---

## 📋 Current Agent Card Styling

**File:** `frontend/src/components/agents/AgentCard.tsx` (lines 24-69)

### Current Style Configuration

```typescript
const useStyles = makeStyles({
  card: {
    height: '100%',  // ← Currently fills container
    cursor: 'pointer',
    transition: 'all 0.2s',
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: tokens.shadow16,
    },
  },
  content: {
    padding: '24px',  // ← Content padding
  },
  title: {
    fontSize: '20px',
    fontWeight: tokens.fontWeightSemibold,
    marginBottom: '12px',
  },
  description: {
    fontSize: '14px',
    lineHeight: '1.5',
    color: tokens.colorNeutralForeground3,
    marginBottom: '20px',
    minHeight: '80px',  // ← Description minimum height
  },
  badges: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    marginBottom: '16px',
  },
  stats: {
    display: 'flex',
    gap: '16px',
    marginBottom: '16px',
    fontSize: '12px',
    color: tokens.colorNeutralForeground3,
  },
  // ... more styles
});
```

---

## 🎯 What Needs to Change

### Option 1: Set Minimum Height (Recommended for consistency)

Add minimum height to card to ensure consistent sizing:

```typescript
const useStyles = makeStyles({
  card: {
    height: '100%',
    minHeight: '400px',  // ← ADD THIS
    cursor: 'pointer',
    transition: 'all 0.2s',
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: tokens.shadow16,
    },
  },
  // ... rest of styles
});
```

**Why:** Ensures all cards have minimum height even with short descriptions, prevents awkward UI with mixed sizes.

### Option 2: Set Fixed Height

For perfectly uniform cards:

```typescript
const useStyles = makeStyles({
  card: {
    height: '450px',  // ← Change from '100%' to fixed size
    cursor: 'pointer',
    transition: 'all 0.2s',
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: tokens.shadow16,
    },
  },
  // ... rest of styles
});
```

**Why:** All cards same exact size, makes grid look very uniform.

### Option 3: Increase Description Height (Simpler alternative)

Keep card responsive but show more text:

```typescript
const useStyles = makeStyles({
  // ... other styles
  description: {
    fontSize: '14px',
    lineHeight: '1.5',
    color: tokens.colorNeutralForeground3,
    marginBottom: '20px',
    minHeight: '120px',  // ← INCREASE from 80px to 120px
  },
  // ... rest of styles
});
```

**Why:** Simpler change, less disruptive, still improves spacing.

---

## 🔍 Component Structure to Understand

**AgentCard.tsx layout:**
```
<Card className={styles.card}>                    ← Main card container
  <div className={styles.content}>                ← Content wrapper
    <CardHeader>
      <div className={styles.title}>              ← Agent name
      <div className={styles.badges}>             ← Status, model, etc.
    </div>
    <p className={styles.description}>            ← Description text
    <div className={styles.stats}>                ← Runs, tokens, latency
    <div className={styles.tools}>                ← Tool badges
    <div className={styles.actions}>              ← Chat, Edit buttons
  </div>
</Card>
```

---

## 📊 Current Heights in Grid

**Where cards are used:**
- File: `frontend/src/pages/AgentsPage.tsx`
- Line 229: `<AgentCard key={agent.id} agent={agent} onAgentDeleted={handleAgentDeleted} />`

**Grid configuration likely in:**
- `AgentsPage.tsx` → search for `display: grid` or `display: flex`
- CSS class or style on parent container

---

## 🎨 Recommended Approach

**Best practice for card height:**

```typescript
const useStyles = makeStyles({
  card: {
    height: '100%',
    minHeight: '400px',  // ← ADD THIS - ensures minimum size
    maxHeight: '600px',  // ← OPTIONAL - prevents overly tall cards
    cursor: 'pointer',
    transition: 'all 0.2s',
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: tokens.shadow16,
    },
  },
  content: {
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    height: '100%',  // ← Ensure content fills card
  },
  description: {
    fontSize: '14px',
    lineHeight: '1.5',
    color: tokens.colorNeutralForeground3,
    marginBottom: '20px',
    minHeight: '100px',  // ← Also increase
    flex: '1',           // ← Allow to grow if space available
  },
  // ... rest of styles
});
```

**Benefits:**
✅ Responsive design preserved  
✅ Minimum size ensures consistency  
✅ Cards don't get too tall  
✅ Description area can expand  
✅ Content flex layout works better  

---

## 🧪 Testing After Change

1. **View Agents Page**
   - Check card heights are consistent
   - Verify hover animation still works
   - Test with different agent descriptions (short/long)

2. **Check Responsive Design**
   - Mobile: cards should stack vertically
   - Tablet: 2 columns
   - Desktop: full grid

3. **Verify Grid Layout**
   - No gaps or misalignment
   - Badges wrap properly
   - Tools display correctly

---

## 💾 Implementation Checklist

- [ ] Open `frontend/src/components/agents/AgentCard.tsx`
- [ ] Locate `useStyles` makeStyles definition (line ~24)
- [ ] Add `minHeight: '400px'` to `card` style (or your preferred height)
- [ ] Optionally add `maxHeight: '600px'` to prevent over-tall cards
- [ ] Optionally increase `description.minHeight` from 80px to 100px
- [ ] Save file
- [ ] Run `npm run dev` in frontend directory
- [ ] Test on agents page to verify appearance
- [ ] Commit changes to git

---

## 📝 Suggested Commit Message

```
feat(frontend): increase agent card minimum height for better visibility

- Set card minHeight to 400px for consistent sizing
- Improves readability of agent descriptions
- Maintains responsive grid layout
- Cards now have better visual balance
```

---

## 🔗 Related Files

**Style Definition:**
- `frontend/src/components/agents/AgentCard.tsx` - Main card component

**Usage:**
- `frontend/src/pages/AgentsPage.tsx` - Where cards are rendered in grid

**Grid Parent (likely needs checking):**
- Look for grid container around AgentCard rendering
- May need to adjust gap or column sizing too

---

## ✨ Visual Impact

### Before
```
┌─────────────────────┐
│ SQL Agent           │
│ ✅ ACTIVE  v4       │
│                     │ ← Short card
│ Description...      │
│ 150 Runs, 12.5K T   │
│ [Chat] [Edit]       │
└─────────────────────┘
```

### After (with minHeight: 400px)
```
┌─────────────────────┐
│ SQL Agent           │
│ ✅ ACTIVE  v4       │
│ Private             │
│                     │
│ Description text    │
│ that can be more    │
│ readable with       │
│ better spacing      │
│                     │
│ 150 Runs, 12.5K T   │
│ 42ms Avg Latency    │
│ 🔌 mcp 🌐 api       │
│ [Chat] [Edit]       │
└─────────────────────┘
```

---

## 🎓 Notes

- **FluentUI Tokens:** Uses `tokens` for spacing, colors (system-wide consistency)
- **Makeshift Styles:** `makeStyles` from FluentUI (not CSS-in-JS like styled-components)
- **Responsive:** Base `height: '100%'` makes cards fill grid cells
- **Animation:** Already has hover effect, height change is smooth
- **Grid Layout:** Check parent container in AgentsPage for grid-template-columns

---

**Ready to implement!** Just modify the `card` and optionally `description` styles in the useStyles definition.
