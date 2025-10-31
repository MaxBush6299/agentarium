/**
 * RFQ Request Form Component
 * 
 * Custom form for initiating RFQ (Request for Quotation) workflows.
 * Replaces standard chat input when rfq-procurement workflow is selected.
 * 
 * Features:
 * - Product details (name, quantity, category)
 * - Multi-select certifications
 * - Delivery date picker
 * - Budget constraints
 * - Auto-populated requestor info
 */

import React, { useState } from 'react'
import {
  Button,
  Input,
  Textarea,
  Dropdown,
  Option,
  makeStyles,
  shorthands,
  tokens,
  Field,
} from '@fluentui/react-components'
import { Send24Regular, ChevronUp24Regular, ChevronDown24Regular } from '@fluentui/react-icons'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    borderTop: '1px solid #2d3e4a',
    background: 'linear-gradient(180deg, #1a2530 0%, #243240 100%)',
    boxShadow: '0 -2px 8px rgba(27, 137, 187, 0.15)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalXL),
    borderBottom: '1px solid #2d3e4a',
    cursor: 'pointer',
    ':hover': {
      backgroundColor: 'rgba(122, 212, 240, 0.05)',
    },
  },
  formContent: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap(tokens.spacingVerticalM),
    ...shorthands.padding(tokens.spacingVerticalL, tokens.spacingHorizontalXL),
    maxHeight: '60vh',
    overflowY: 'auto',
  },
  collapsed: {
    display: 'none',
  },
  formTitle: {
    fontSize: tokens.fontSizeBase400,
    fontWeight: tokens.fontWeightSemibold,
    color: '#7ad4f0',
  },
  toggleButton: {
    minWidth: 'auto',
    ...shorthands.padding('4px'),
  },
  formGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    ...shorthands.gap(tokens.spacingVerticalM, tokens.spacingHorizontalL),
  },
  fullWidth: {
    gridColumn: '1 / -1',
  },
  fieldLabel: {
    color: '#bdeffc',
    fontSize: tokens.fontSizeBase300,
    marginBottom: tokens.spacingVerticalXS,
  },
  submitRow: {
    display: 'flex',
    justifyContent: 'flex-end',
    ...shorthands.gap(tokens.spacingHorizontalM),
    marginTop: tokens.spacingVerticalM,
    paddingTop: tokens.spacingVerticalM,
    borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
  },
  readOnlyField: {
    backgroundColor: tokens.colorNeutralBackground5,
    opacity: 0.8,
  },
})

interface RFQRequestFormProps {
  onSubmit: (rfqData: RFQFormData) => void
  disabled?: boolean
  userEmail?: string
  userName?: string
}

export interface RFQFormData {
  request_id: string
  product_id: string
  product_name: string
  category: string
  quantity: number
  unit: string
  required_certifications: string[]
  special_requirements: string
  desired_delivery_date: string
  max_lead_time_days: number
  budget_amount: number
  requestor_name: string
  requestor_email: string
}

// Predefined options
const CATEGORIES = [
  { key: 'industrial_sensors', text: 'Industrial Sensors' },
  { key: 'electronic_components', text: 'Electronic Components' },
  { key: 'mechanical_parts', text: 'Mechanical Parts' },
  { key: 'raw_materials', text: 'Raw Materials' },
  { key: 'safety_equipment', text: 'Safety Equipment' },
  { key: 'office_supplies', text: 'Office Supplies' },
]

const CERTIFICATIONS = [
  'ISO-9001',
  'ISO-14001',
  'CE',
  'UL',
  'RoHS',
  'REACH',
  'FDA',
  'IATF-16949',
]

const UNITS = [
  { key: 'pieces', text: 'Pieces' },
  { key: 'units', text: 'Units' },
  { key: 'kg', text: 'Kilograms' },
  { key: 'liters', text: 'Liters' },
  { key: 'meters', text: 'Meters' },
  { key: 'boxes', text: 'Boxes' },
]

export const RFQRequestForm: React.FC<RFQRequestFormProps> = ({
  onSubmit,
  disabled = false,
  userEmail = 'procurement@company.com',
  userName = 'Procurement Manager',
}) => {
  const styles = useStyles()

  // Collapse state
  const [isExpanded, setIsExpanded] = useState(true)

  // Form state
  const [productName, setProductName] = useState('High-Precision Industrial Sensors')
  const [category, setCategory] = useState('industrial_sensors')
  const [quantity, setQuantity] = useState(1000)
  const [unit, setUnit] = useState('pieces')
  const [certifications, setCertifications] = useState<string[]>(['ISO-9001'])
  const [specialRequirements, setSpecialRequirements] = useState('Temperature range: -40°C to 85°C, Accuracy: ±0.1°C')
  const [deliveryDate, setDeliveryDate] = useState(() => {
    // Default to 30 days from now
    const date = new Date()
    date.setDate(date.getDate() + 30)
    return date.toISOString().split('T')[0]
  })
  const [maxLeadTime, setMaxLeadTime] = useState(30)
  const [budget, setBudget] = useState(100000)

  const handleSubmit = () => {
    // Generate IDs
    const timestamp = new Date().getTime()
    const requestId = `RFQ-${new Date().toISOString().split('T')[0].replace(/-/g, '')}-${timestamp.toString().slice(-6)}`
    const productId = `PROD-${category.toUpperCase()}-${timestamp.toString().slice(-6)}`

    const rfqData: RFQFormData = {
      request_id: requestId,
      product_id: productId,
      product_name: productName,
      category,
      quantity,
      unit,
      required_certifications: certifications,
      special_requirements: specialRequirements,
      desired_delivery_date: deliveryDate,
      max_lead_time_days: maxLeadTime,
      budget_amount: budget,
      requestor_name: userName,
      requestor_email: userEmail,
    }

    onSubmit(rfqData)
  }

  const handleCertificationChange = (_event: any, data: any) => {
    const selected = data.selectedOptions || []
    setCertifications(selected)
  }

  const isFormValid = 
    productName.trim() !== '' &&
    quantity > 0 &&
    budget > 0

  return (
    <div className={styles.container}>
      {/* Collapsible Header */}
      <div className={styles.header} onClick={() => setIsExpanded(!isExpanded)}>
        <div className={styles.formTitle}>
          📋 RFQ Request Form
        </div>
        <Button
          appearance="subtle"
          icon={isExpanded ? <ChevronDown24Regular /> : <ChevronUp24Regular />}
          className={styles.toggleButton}
          aria-label={isExpanded ? "Collapse form" : "Expand form"}
        />
      </div>

      {/* Form Content */}
      <div className={`${styles.formContent} ${!isExpanded ? styles.collapsed : ''}`}>
        <div className={styles.formGrid}>
          {/* Product Name */}
          <Field label="Product Name" required className={styles.fullWidth}>
            <Input
              value={productName}
              onChange={(_, data) => setProductName(data.value)}
              placeholder="Enter product name..."
              disabled={disabled}
            />
          </Field>

          {/* Category */}
          <Field label="Category" required>
            <Dropdown
              placeholder="Select category"
              value={CATEGORIES.find(c => c.key === category)?.text || ''}
              selectedOptions={[category]}
              onOptionSelect={(_, data) => setCategory(data.optionValue as string)}
              disabled={disabled}
            >
              {CATEGORIES.map((cat) => (
                <Option key={cat.key} value={cat.key}>
                  {cat.text}
                </Option>
              ))}
          </Dropdown>
        </Field>

        {/* Quantity */}
        <Field label="Quantity" required>
          <Input
            type="number"
            value={quantity.toString()}
            onChange={(_, data) => setQuantity(parseInt(data.value) || 0)}
            min={1}
            disabled={disabled}
          />
        </Field>

        {/* Unit */}
        <Field label="Unit">
          <Dropdown
            placeholder="Select unit"
            value={UNITS.find(u => u.key === unit)?.text || ''}
            selectedOptions={[unit]}
            onOptionSelect={(_, data) => setUnit(data.optionValue as string)}
            disabled={disabled}
          >
            {UNITS.map((u) => (
              <Option key={u.key} value={u.key}>
                {u.text}
              </Option>
            ))}
          </Dropdown>
        </Field>

        {/* Certifications */}
        <Field label="Required Certifications" className={styles.fullWidth}>
          <Dropdown
            placeholder="Select certifications..."
            multiselect
            selectedOptions={certifications}
            onOptionSelect={handleCertificationChange}
            disabled={disabled}
          >
            {CERTIFICATIONS.map((cert) => (
              <Option key={cert} value={cert}>
                {cert}
              </Option>
            ))}
          </Dropdown>
        </Field>

        {/* Special Requirements */}
        <Field label="Special Requirements / Technical Specifications" className={styles.fullWidth}>
          <Textarea
            value={specialRequirements}
            onChange={(_, data) => setSpecialRequirements(data.value)}
            placeholder="Enter technical specs, quality requirements, etc."
            rows={3}
            disabled={disabled}
            resize="vertical"
          />
        </Field>

        {/* Delivery Date */}
        <Field label="Desired Delivery Date">
          <Input
            type="date"
            value={deliveryDate}
            onChange={(_, data) => setDeliveryDate(data.value)}
            disabled={disabled}
          />
        </Field>

        {/* Max Lead Time */}
        <Field label="Max Lead Time (days)">
          <Input
            type="number"
            value={maxLeadTime.toString()}
            onChange={(_, data) => setMaxLeadTime(parseInt(data.value) || 0)}
            min={1}
            disabled={disabled}
          />
        </Field>

        {/* Budget */}
        <Field label="Budget Amount ($)" required className={styles.fullWidth}>
          <Input
            type="number"
            value={budget.toString()}
            onChange={(_, data) => setBudget(parseFloat(data.value) || 0)}
            min={0}
            step={1000}
            disabled={disabled}
          />
        </Field>

        {/* Requestor Info (Read-only) */}
        <Field label="Requestor Name" hint="Auto-populated from your profile">
          <Input
            value={userName}
            readOnly
            className={styles.readOnlyField}
            disabled={disabled}
          />
        </Field>

        <Field label="Requestor Email" hint="Auto-populated from your profile">
          <Input
            value={userEmail}
            readOnly
            className={styles.readOnlyField}
            disabled={disabled}
          />
        </Field>
        </div>

        {/* Submit */}
        <div className={styles.submitRow}>
          <Button
            appearance="primary"
            icon={<Send24Regular />}
            onClick={handleSubmit}
            disabled={!isFormValid || disabled}
            size="large"
          >
            {disabled ? 'Processing RFQ...' : 'Submit RFQ Request'}
          </Button>
        </div>
      </div>
    </div>
  )
}
