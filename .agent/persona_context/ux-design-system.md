---
status: DRAFT
version: 1.0
last_updated: 2026-01-17T15:28:00+05:30
persona: UX Design Lead
upstream: product-requirements.md
---

# UX Design System
## E-Commerce Fraud Detection MLOps Platform

## Design Principles

1. **Clarity First** - Complex ML concepts made understandable
2. **Action-Oriented** - Clear paths to complete tasks
3. **Progressive Disclosure** - Show basics first, details on demand
4. **Trust Through Transparency** - Explain why decisions were made

## Color System

| Role | Light Mode | Dark Mode | Usage |
|------|------------|-----------|-------|
| Primary | `#2563EB` | `#3B82F6` | Actions, links |
| Success | `#059669` | `#10B981` | OK status |
| Warning | `#D97706` | `#F59E0B` | Warnings |
| Critical | `#DC2626` | `#EF4444` | Errors, critical |
| Background | `#F9FAFB` | `#111827` | Page bg |
| Surface | `#FFFFFF` | `#1F2937` | Cards |

## Navigation Structure

```
Sidebar (Left):
├── Dashboard        → Overview metrics
├── Data Registry    → Upload, browse datasets
├── Training         → Configure, run training
├── Model Registry   → View, compare, promote
├── Monitoring       → Drift, performance
├── Bias Detection   → Fairness metrics
├── Alerts           → Active alerts
└── Settings         → Config, team
```

## Key Pages

### 1. Dashboard
- 4 metric cards (Models, Datasets, Alerts, Predictions)
- Weekly activity trend chart
- Recent alerts list
- Quick actions: Train, Upload, View Alerts

### 2. Training Page
- Step wizard: Select Dataset → Configure → Train → View Results
- Algorithm selector with descriptions
- Hyperparameter sliders with defaults
- Live training progress with loss curves

### 3. Monitoring Page
- Drift status cards (Data, Concept, Feature)
- Time-series drift charts
- Baseline comparison table
- One-click retrain button

### 4. Bias Detection Page
- Protected attribute selector
- Fairness metrics by group (table + bar chart)
- Status indicators (OK/Warning/Critical)
- Drill-down to individual groups

## Component Library

| Component | Usage |
|-----------|-------|
| MetricCard | Dashboard KPIs |
| StatusBadge | Model status, alert severity |
| DataTable | Datasets, models, predictions |
| LineChart | Time-series metrics |
| BarChart | Feature importance, bias metrics |
| StepWizard | Training flow |
| AlertBanner | Drift/bias warnings |

## Responsive Breakpoints

| Size | Width | Layout |
|------|-------|--------|
| Mobile | < 640px | Collapsed sidebar |
| Tablet | 640-1024px | Mini sidebar |
| Desktop | > 1024px | Full sidebar |

## Accessibility

- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader friendly labels
- Color contrast 4.5:1 minimum

*Document prepared by: UX Design Lead Persona*
