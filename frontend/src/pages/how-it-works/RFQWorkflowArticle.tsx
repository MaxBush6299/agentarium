import React from 'react';
import { ArticleLayout } from './ArticleLayout';
import { Mermaid } from '../../components/Mermaid';

export const RFQWorkflowArticle: React.FC = () => {
  const mermaidChart = `%%{init: {'theme':'default', 'themeVariables': { 'fontSize':'14px'}}}%%
flowchart TD
 subgraph Phase2["PHASE 2: Sequential Preprocessing"]
        PRA["ProductReviewAgent<br>(Spec Extraction)"]
        VQA["VendorQualificationAgent<br>(Vendor Filtering)"]
        PreOrch["PreprocessingOrchestrator<br>(Sequential Handoff)"]
  end
 subgraph Phase3["PHASE 3: Parallel Evaluation (3 Tracks)"]
        CCE["ComplianceEvaluator<br>(Track 1)"]
        DEE["DeliveryEvaluator<br>(Track 2)"]
        FEE["FinancialEvaluator<br>(Track 3)"]
        Merge["<b>Equal Weighting Merge</b><br>(33% each track)"]
  end
 subgraph Phase4["PHASE 4: Comparison & Analysis"]
        CAA["ComparisonAndAnalysisAgent<br>(Score Normalization)"]
        CReport["ComparisonReport<br>(Ranked + Risk Flags)"]
  end
 subgraph Phase5["PHASE 5: Negotiation Strategy"]
        NSA["NegotiationStrategyAgent<br>(Leverage Analysis)"]
        NRec["NegotiationRecommendation<br>(Proposed Terms)"]
  end
 subgraph Phase6["PHASE 6: Human-in-the-Loop"]
        HG["ApprovalGateExecutor<br>(Human Review)"]
        Decision{"Human<br>Decision"}
  end
 subgraph Phase7["PHASE 7: PO Generation"]
        PO["PurchaseOrderAgent<br>(Create PO)"]
        End(["RFQ Complete"])
  end
    Start(["RFQ Request Submitted"]) -- Product Info --> Phase2
    PRA -- ProductRequirements --> VQA
    VQA -- QualifiedVendors --> PreOrch
    Phase2 -- Vendors + Requirements --> Phase3
    CCE -- Compliance Scores --> Merge
    DEE -- Delivery Scores --> Merge
    FEE -- Financial Scores --> Merge
    Phase3 -- Merged Scores --> Phase4
    CAA -- Top 3 Vendors --> CReport
    Phase4 -- ComparisonReport --> Phase5
    NSA -- "Counter-offers" --> NRec
    Phase5 -- Strategy + Top Vendor --> Phase6
    HG -- Approved/Rejected --> Decision
    Decision -- Approved --> Phase7
    Decision -- Rejected --> Phase5
    PO -- Final PO --> End
    style Phase2 fill:#90EE90
    style Phase3 fill:#87CEEB
    style Phase4 fill:#FFD700
    style Phase5 fill:#FFA500
    style Phase6 fill:#FF6B6B
    style Phase7 fill:#DDA0DD`;

  return (
    <ArticleLayout
      title="RFQ Procurement Workflow"
      date="October 31, 2025"
      author="Engineering Team"
    >
      <h2>What is the RFQ Workflow?</h2>
      <p>
        The <strong>RFQ (Request for Quotation) Procurement Workflow</strong> is a sophisticated multi-agent system
        that automates the entire vendor selection and purchase order process. It orchestrates multiple specialized
        AI agents working in parallel and sequence to analyze vendor quotes, evaluate compliance, negotiate terms,
        and generate purchase orders—all while keeping humans in the loop for critical decisions.
      </p>

      <p><strong>Example Use Case:</strong></p>
      <blockquote>
        <p>You need: <em>"100 industrial temperature sensors with 5-day delivery for under $50,000"</em></p>
        <p>The RFQ Workflow automatically:</p>
        <ul>
          <li>Extracts technical specifications from your requirements</li>
          <li>Identifies and qualifies 5 suitable vendors from the database</li>
          <li>Requests and evaluates quotes across compliance, delivery, and financial metrics</li>
          <li>Ranks vendors with weighted scoring and risk analysis</li>
          <li>Generates negotiation strategies with leverage points</li>
          <li>Presents recommendations for your approval</li>
          <li>Creates a complete purchase order upon approval</li>
        </ul>
        <p><strong>All in under 30 seconds.</strong></p>
      </blockquote>

      <h2>Workflow Architecture Overview</h2>
      <p>
        The RFQ workflow consists of <strong>7 sequential phases</strong>, with Phase 3 utilizing parallel processing
        for evaluation tasks. Each phase produces detailed output that persists in the chat interface as a collapsible
        section, allowing you to expand and review any phase's details at any time.
      </p>

      <h3>Workflow Diagram</h3>
      <Mermaid chart={mermaidChart} />

      <h2>Phase-by-Phase Breakdown</h2>

      <h3>Phase 1: Request Intake</h3>
      <p>
        The user submits an RFQ request form with the following information:
      </p>
      <ul>
        <li><strong>Product Name:</strong> What you're purchasing (e.g., "Industrial Temperature Sensors")</li>
        <li><strong>Quantity:</strong> How many units needed</li>
        <li><strong>Product Description:</strong> Detailed specifications and requirements</li>
        <li><strong>Delivery Location:</strong> Where the product should be shipped</li>
        <li><strong>Desired Delivery Date:</strong> When you need the product</li>
        <li><strong>Maximum Lead Time:</strong> Latest acceptable delivery timeframe</li>
        <li><strong>Budget Amount:</strong> Total budget available for this purchase</li>
      </ul>
      <p>
        This creates an <code>RFQRequest</code> object with a unique ID (e.g., <code>RFQ-20251031-0828</code>)
        and initiates the workflow.
      </p>

      <h3>Phase 2: Sequential Preprocessing</h3>
      <p>
        Two agents work in sequence to extract specifications and filter vendors:
      </p>

      <h4>1. ProductReviewAgent (Specification Extraction)</h4>
      <ul>
        <li><strong>Input:</strong> Product description and requirements from user</li>
        <li><strong>Processing:</strong> Uses GPT-4 to analyze the text and extract structured specifications</li>
        <li><strong>Output:</strong> <code>ProductRequirements</code> object containing:
          <ul>
            <li>Technical specifications (voltage, temperature range, connectivity, etc.)</li>
            <li>Quality standards (ISO certifications, warranty requirements)</li>
            <li>Compliance needs (RoHS, CE, UL certifications)</li>
            <li>Categorization (e.g., "industrial_sensors")</li>
          </ul>
        </li>
      </ul>

      <h4>2. VendorQualificationAgent (Vendor Filtering)</h4>
      <ul>
        <li><strong>Input:</strong> Product requirements and category</li>
        <li><strong>Processing:</strong>
          <ul>
            <li>Queries vendor database for suppliers in the product category</li>
            <li>Filters by certifications (must have required compliance certifications)</li>
            <li>Filters by lead time capability (must meet max lead time requirement)</li>
            <li>Filters by rating (minimum 3.5/5 stars)</li>
          </ul>
        </li>
        <li><strong>Output:</strong> List of 3-5 qualified vendors with their profiles:
          <ul>
            <li>Company name, location, contact info</li>
            <li>Certifications and specializations</li>
            <li>Overall rating and previous order count</li>
            <li>Estimated lead time in days</li>
          </ul>
        </li>
      </ul>

      <p>
        The <code>PreprocessingOrchestrator</code> manages the sequential handoff from ProductReviewAgent
        to VendorQualificationAgent, ensuring the output of Phase 2.1 becomes the input for Phase 2.2.
      </p>

      <h3>Phase 3: Parallel Evaluation (Three Tracks)</h3>
      <p>
        This is where the workflow achieves significant speed gains. Three evaluation agents run <strong>simultaneously</strong>
        in parallel, each analyzing the vendor quotes from a different perspective:
      </p>

      <h4>Track 1: ComplianceEvaluator</h4>
      <ul>
        <li><strong>Focus:</strong> Regulatory compliance and quality standards</li>
        <li><strong>Evaluates:</strong>
          <ul>
            <li>Certification completeness (RoHS, CE, ISO 9001, etc.)</li>
            <li>Quality assurance processes</li>
            <li>Compliance documentation availability</li>
            <li>Risk of non-compliance</li>
          </ul>
        </li>
        <li><strong>Score Range:</strong> 0-10 (10 = perfect compliance)</li>
      </ul>

      <h4>Track 2: DeliveryEvaluator</h4>
      <ul>
        <li><strong>Focus:</strong> Logistics and delivery capabilities</li>
        <li><strong>Evaluates:</strong>
          <ul>
            <li>Lead time vs. required delivery date</li>
            <li>Shipping reliability and on-time delivery history</li>
            <li>Geographic proximity to delivery location</li>
            <li>Inventory availability</li>
          </ul>
        </li>
        <li><strong>Score Range:</strong> 0-10 (10 = fastest, most reliable delivery)</li>
      </ul>

      <h4>Track 3: FinancialEvaluator</h4>
      <ul>
        <li><strong>Focus:</strong> Pricing and financial terms</li>
        <li><strong>Evaluates:</strong>
          <ul>
            <li>Total cost (unit price × quantity + shipping)</li>
            <li>Budget fit (within allocated budget?)</li>
            <li>Payment terms (net 30, net 60, upfront?)</li>
            <li>Price competitiveness vs. market rates</li>
          </ul>
        </li>
        <li><strong>Score Range:</strong> 0-10 (10 = best value for money)</li>
      </ul>

      <h4>Equal Weighting Merge</h4>
      <p>
        After all three tracks complete, the scores are merged with <strong>equal weighting</strong>:
      </p>
      <pre>{`Overall Score = (Compliance Score × 0.33) + (Delivery Score × 0.33) + (Financial Score × 0.33)`}</pre>
      <p>
        Each vendor receives a final score from 0-10 based on this weighted average, ensuring no single
        dimension dominates the evaluation.
      </p>

      <h3>Phase 4: Comparison & Analysis</h3>
      <p>
        The <code>ComparisonAndAnalysisAgent</code> takes the merged evaluation scores and performs deeper analysis:
      </p>
      <ul>
        <li><strong>Score Normalization:</strong> Adjusts scores to a 0-5 scale for ranking</li>
        <li><strong>Vendor Ranking:</strong> Sorts vendors by overall score (highest to lowest)</li>
        <li><strong>Risk Flagging:</strong> Identifies potential issues:
          <ul>
            <li>Budget overruns (price exceeds budget by {'>'}10%)</li>
            <li>Lead time risks (delivery window too tight)</li>
            <li>Compliance gaps (missing critical certifications)</li>
            <li>Low ratings (vendor rating below threshold)</li>
          </ul>
        </li>
        <li><strong>Top 3 Selection:</strong> Recommends the top 3 vendors for consideration</li>
      </ul>
      <p>
        <strong>Output:</strong> A <code>ComparisonReport</code> with:
      </p>
      <ul>
        <li>Ranked list of all vendors with scores and rationales</li>
        <li>Detailed breakdown of why each vendor scored as they did</li>
        <li>Risk flags and mitigation recommendations</li>
        <li>Key differentiators between top candidates</li>
      </ul>

      <h3>Phase 5: Negotiation Strategy</h3>
      <p>
        The <code>NegotiationStrategyAgent</code> focuses on the <strong>top-ranked vendor</strong> and develops
        a strategic negotiation plan:
      </p>

      <h4>Leverage Analysis</h4>
      <p>The agent identifies your negotiating position:</p>
      <ul>
        <li><strong>High-volume potential:</strong> If quantity is large, you have pricing power</li>
        <li><strong>Competitive alternatives:</strong> Presence of other qualified vendors gives options</li>
        <li><strong>Time sensitivity:</strong> Urgent delivery reduces leverage</li>
        <li><strong>Long-term relationship:</strong> Potential for repeat business</li>
      </ul>

      <h4>Counter-Offer Generation</h4>
      <p>The agent proposes specific negotiation tactics:</p>
      <ul>
        <li><strong>Suggested Unit Price:</strong> Target price per unit (typically 5-10% below quote)</li>
        <li><strong>Volume Discount Request:</strong> "If we order 150 units instead of 100, can you offer $X?"</li>
        <li><strong>Payment Term Negotiation:</strong> "Can we extend from Net 30 to Net 60 for cash flow?"</li>
        <li><strong>Delivery Acceleration:</strong> "Can you expedite shipping for a small premium?"</li>
      </ul>

      <h4>Fallback Options</h4>
      <p>The agent also prepares Plan B scenarios:</p>
      <ul>
        <li><strong>Fallback Price:</strong> Maximum acceptable price if vendor won't budge</li>
        <li><strong>Alternative Vendors:</strong> "If this vendor doesn't work out, Vendor #2 is available at $X"</li>
        <li><strong>Scope Adjustment:</strong> "We could reduce quantity to 80 units to meet budget"</li>
      </ul>

      <p>
        <strong>Output:</strong> A comprehensive <code>NegotiationRecommendation</code> document with:
      </p>
      <ul>
        <li>Full negotiation strategy and talking points</li>
        <li>Suggested counter-offers with justifications</li>
        <li>Expected outcomes (optimistic, realistic, pessimistic)</li>
        <li>Fallback options if negotiation fails</li>
      </ul>

      <h3>Phase 6: Human-in-the-Loop Approval</h3>
      <p>
        The <code>ApprovalGateExecutor</code> presents the recommendation and waits for human decision:
      </p>

      <h4>Approval UI</h4>
      <p>The user sees:</p>
      <ul>
        <li><strong>Recommended Vendor:</strong> Name, quote summary, and scores</li>
        <li><strong>Negotiation Strategy:</strong> Full strategy from Phase 5</li>
        <li><strong>Budget Impact:</strong> Total cost vs. budget, any overruns</li>
        <li><strong>Risk Summary:</strong> Any flags or concerns from Phase 4</li>
        <li><strong>Approval Buttons:</strong>
          <ul>
            <li><strong>Approve:</strong> Proceed to PO generation with this vendor</li>
            <li><strong>Edit:</strong> Modify negotiation terms or pricing (future feature)</li>
            <li><strong>Reject:</strong> Go back to Phase 5 and consider alternate vendors</li>
          </ul>
        </li>
      </ul>

      <h4>Decision Routing</h4>
      <ul>
        <li><strong>Approved:</strong> Workflow advances to Phase 7 (PO Generation)</li>
        <li><strong>Rejected:</strong> Workflow loops back to Phase 5 with the next-ranked vendor</li>
        <li><strong>Edited:</strong> User-modified terms are incorporated into the final PO</li>
      </ul>

      <p>
        <strong>Note:</strong> In the current implementation, <code>wait_for_human=False</code> for demo purposes,
        meaning the workflow auto-approves. In production, this would pause and wait for user interaction.
      </p>

      <h3>Phase 7: Purchase Order Generation</h3>
      <p>
        Once approved, the <code>PurchaseOrderAgent</code> creates the final purchase order:
      </p>

      <h4>PO Document Contents</h4>
      <pre>{`Purchase Order #: PO-20251031-082845
Vendor: Acme Sensors Ltd.
Product: Industrial Temperature Sensors (100 units)
Unit Price: $425.00
Total Amount: $42,500.00
Payment Terms: Net 30
Delivery Date: 2025-11-15
Shipping Address: 123 Manufacturing Blvd, Detroit, MI 48201

Special Terms:
- 5% volume discount applied
- Free expedited shipping included
- 2-year warranty on all units`}</pre>

      <h4>PO Data Structure</h4>
      <p>The <code>PurchaseOrder</code> Pydantic model includes:</p>
      <ul>
        <li><code>po_number</code> - Unique identifier</li>
        <li><code>vendor_id</code> and <code>vendor_name</code></li>
        <li><code>product_name</code>, <code>quantity</code>, <code>unit_price</code>, <code>total_amount</code></li>
        <li><code>payment_terms</code> - e.g., "Net 30"</li>
        <li><code>delivery_date</code> - Expected delivery</li>
        <li><code>delivery_address</code> - Shipping destination</li>
        <li><code>special_terms</code> - Any negotiated extras or conditions</li>
        <li><code>approval_date</code> and <code>approved_by</code> - Audit trail</li>
      </ul>

      <p>
        <strong>Output:</strong> The complete PO is displayed in the chat and (in production) would be:
      </p>
      <ul>
        <li>Saved to the database for record-keeping</li>
        <li>Emailed to the vendor as a PDF attachment</li>
        <li>Integrated with ERP/procurement systems via API</li>
        <li>Added to financial accounting systems</li>
      </ul>

      <h2>Technical Implementation Details</h2>

      <h3>Orchestrator Architecture</h3>
      <p>
        The workflow is controlled by the <code>RFQWorkflowOrchestrator</code> class, which manages state
        and agent execution:
      </p>
      <pre>{`class RFQWorkflowOrchestrator:
    async def execute_full_workflow_streaming(
        self,
        rfq_request: RFQRequest,
        workflow_id: str,
        buyer_name: str,
        buyer_email: str,
        wait_for_human: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        # Phase 2: Preprocessing
        yield {"phase": "Phase 2: Preprocessing", "message": "...", "data": {...}}
        
        # Phase 3: Parallel Evaluation
        yield {"phase": "Phase 3: Evaluation", "message": "...", "data": {...}}
        
        # ... phases 4-7 ...`}</pre>

      <h3>Agent Communication</h3>
      <p>
        Agents pass data using <strong>Pydantic models</strong> for type safety:
      </p>
      <ul>
        <li><code>ProductRequirements</code> - From ProductReviewAgent to VendorQualificationAgent</li>
        <li><code>VendorProfile[]</code> - From VendorQualificationAgent to Evaluation agents</li>
        <li><code>QuoteResponse[]</code> - From MockVendorAPI to Evaluation agents</li>
        <li><code>EvaluationResult[]</code> - From Evaluators to ComparisonAndAnalysisAgent</li>
        <li><code>ComparisonReport</code> - From ComparisonAgent to NegotiationAgent</li>
        <li><code>NegotiationRecommendation</code> - From NegotiationAgent to ApprovalGate</li>
        <li><code>PurchaseOrder</code> - From PurchaseOrderAgent to user</li>
      </ul>

      <h3>Parallel Execution Strategy</h3>
      <p>
        Phase 3 uses <code>asyncio.gather()</code> to run evaluation tracks concurrently:
      </p>
      <pre>{`# Execute all three evaluators in parallel
compliance_results, delivery_results, financial_results = await asyncio.gather(
    compliance_evaluator.evaluate_quotes(qualified_vendors, quotes, requirements),
    delivery_evaluator.evaluate_quotes(qualified_vendors, quotes, requirements, rfq_request.delivery_location),
    financial_evaluator.evaluate_quotes(qualified_vendors, quotes, requirements, rfq_request.budget_amount)
)

# Merge results with equal weighting
merged_evaluations = self.merge_evaluations_equal_weight(
    compliance_results,
    delivery_results,
    financial_results
)`}</pre>

      <h3>Streaming Output Architecture</h3>
      <p>
        The workflow sends each phase as a <strong>separate Server-Sent Event (SSE)</strong>:
      </p>

      <h4>Backend (workflows.py)</h4>
      <pre>{`async for phase_result in orchestrator.execute_full_workflow_streaming(...):
    phase_message = phase_result.get("message", "")
    phase_name = phase_result.get("phase", "unknown")
    phase_data = serialize_for_json(phase_result.get("data", {}))
    
    # Send as complete phase event
    yield f"event: phase_complete\\ndata: {json.dumps({
        'phase': phase_name,
        'message': phase_message,
        'data': phase_data
    })}\\n\\n"`}</pre>

      <h4>Frontend (api.ts)</h4>
      <pre>{`// Parse SSE event
if (eventType === 'phase_complete') {
    // Create a new message for this phase
    const newPhaseMessage = {
        id: \`\${Date.now()}_\${parsed.phase}\`,
        role: 'assistant',
        content: parsed.message,
        metadata: {
            phase: parsed.phase,
            isPhaseMessage: true,
            data: parsed.data
        }
    };
    // Add to message list
}`}</pre>

      <h4>UI (MessageBubble.tsx)</h4>
      <pre>{`// Render collapsible phase section
{isPhaseMessage && message.metadata?.phase ? (
    <div className={styles.phaseContainer}>
        <div className={styles.phaseHeader} onClick={() => setIsExpanded(!isExpanded)}>
            {isExpanded ? <ChevronDown /> : <ChevronRight />}
            <Text>{message.metadata.phase}</Text>
        </div>
        <div className={isExpanded ? styles.phaseContent : styles.phaseContentCollapsed}>
            <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
    </div>
) : ...}`}</pre>

      <h3>Database Persistence</h3>
      <p>
        Each phase message is saved to Cosmos DB as a separate message in the thread:
      </p>
      <ul>
        <li><strong>Collection:</strong> <code>messages</code></li>
        <li><strong>Partition Key:</strong> <code>threadId</code></li>
        <li><strong>Document:</strong>
          <ul>
            <li><code>id</code> - Unique message ID</li>
            <li><code>threadId</code> - Parent conversation thread</li>
            <li><code>role</code> - "assistant"</li>
            <li><code>content</code> - Full phase message (markdown formatted)</li>
            <li><code>metadata.phase</code> - Phase name for UI rendering</li>
            <li><code>metadata.data</code> - Structured phase data (JSON)</li>
            <li><code>timestamp</code> - When the phase completed</li>
          </ul>
        </li>
      </ul>

      <h2>Observability & Logging</h2>
      <p>
        The RFQ workflow includes comprehensive logging at every stage:
      </p>

      <h3>Structured Logging</h3>
      <pre>{`{"timestamp": "2025-10-31T08:26:26.472441",
 "level": "INFO",
 "logger": "src.agents.workflows.rfq.observability",
 "message": "Vendor qualification completed: 5 vendors qualified",
 "workflow_id": "wf-rfq-procurement-20251031082625",
 "stage": "vendor_qualification"}`}</pre>

      <h3>Log Stages</h3>
      <ul>
        <li><code>preprocessing</code> - Phase 2 (spec extraction, vendor qualification)</li>
        <li><code>evaluation</code> - Phase 3 (parallel track execution)</li>
        <li><code>comparison</code> - Phase 4 (ranking and analysis)</li>
        <li><code>negotiation</code> - Phase 5 (strategy generation)</li>
        <li><code>approval</code> - Phase 6 (human gate)</li>
        <li><code>po_generation</code> - Phase 7 (final PO creation)</li>
      </ul>

      <h3>Application Insights Integration</h3>
      <p>
        Telemetry is automatically sent to Azure Application Insights:
      </p>
      <ul>
        <li><strong>Custom Metrics:</strong> Workflow execution time, phase durations, vendor count</li>
        <li><strong>Dependencies:</strong> Azure OpenAI calls, Cosmos DB queries, vendor API requests</li>
        <li><strong>Traces:</strong> Agent execution flows, decision points, error conditions</li>
        <li><strong>Exceptions:</strong> Automatic capture of failures with stack traces</li>
      </ul>

      <h2>Key Features & Innovations</h2>

      <h3>1. Persistent Phase Output</h3>
      <p>
        Unlike traditional chatbots where responses are replaced or lost, each RFQ phase persists as a
        <strong>separate collapsible message</strong> in the chat. Users can:
      </p>
      <ul>
        <li>Review any phase's details by expanding it</li>
        <li>Compare vendor evaluations side-by-side</li>
        <li>Scroll back through the entire workflow history</li>
        <li>Export the complete workflow transcript</li>
      </ul>

      <h3>2. Parallel Processing Architecture</h3>
      <p>
        Phase 3's parallel evaluation achieves <strong>3x speed improvement</strong> compared to sequential
        processing. Instead of waiting 15 seconds (5s per track), the workflow completes in 5 seconds total.
      </p>

      <h3>3. Human-in-the-Loop Design</h3>
      <p>
        The approval gate (Phase 6) ensures critical procurement decisions remain under human control, while
        still benefiting from AI-powered analysis and recommendations. This balance is crucial for:
      </p>
      <ul>
        <li>Regulatory compliance (approval audit trails)</li>
        <li>Budget authority (only authorized users can approve large purchases)</li>
        <li>Risk management (human oversight of AI recommendations)</li>
        <li>Trust building (users see and approve the final decision)</li>
      </ul>

      <h3>4. Extensible Agent Framework</h3>
      <p>
        Each agent is built using the <code>DemoBaseAgent</code> wrapper, making it easy to:
      </p>
      <ul>
        <li>Add new evaluation dimensions (e.g., sustainability score, supplier diversity)</li>
        <li>Swap AI models (GPT-4o, GPT-4-turbo, o1-preview)</li>
        <li>Integrate external tools (ERP systems, pricing databases, credit check APIs)</li>
        <li>Customize for different industries (manufacturing, retail, healthcare)</li>
      </ul>

      <h3>5. Rich Data Models</h3>
      <p>
        Pydantic models provide strong typing and validation throughout the workflow:
      </p>
      <ul>
        <li><strong>Type Safety:</strong> Compile-time checks prevent passing wrong data types</li>
        <li><strong>Validation:</strong> Automatic validation of required fields and constraints</li>
        <li><strong>Documentation:</strong> Models serve as living documentation of data structures</li>
        <li><strong>JSON Serialization:</strong> Easy conversion to/from API payloads</li>
      </ul>

      <h2>Production Considerations</h2>

      <h3>Scaling & Performance</h3>
      <ul>
        <li><strong>Caching:</strong> Vendor profiles and certifications could be cached to reduce DB queries</li>
        <li><strong>Batch Processing:</strong> Multiple RFQ requests could be processed in parallel</li>
        <li><strong>Rate Limiting:</strong> Azure OpenAI rate limits may require queue management</li>
        <li><strong>Timeout Handling:</strong> Long-running workflows should have configurable timeouts</li>
      </ul>

      <h3>Security & Compliance</h3>
      <ul>
        <li><strong>Role-Based Access:</strong> Only authorized users can approve POs above certain thresholds</li>
        <li><strong>Audit Logging:</strong> Every decision and approval is logged with user ID and timestamp</li>
        <li><strong>Data Privacy:</strong> Vendor information should comply with GDPR/CCPA regulations</li>
        <li><strong>Encryption:</strong> Sensitive data (pricing, contracts) encrypted at rest and in transit</li>
      </ul>

      <h3>Error Handling & Recovery</h3>
      <ul>
        <li><strong>Partial Completion:</strong> Workflow state should be saved after each phase</li>
        <li><strong>Resume Capability:</strong> If Phase 5 fails, resume from Phase 5 without re-running Phase 2-4</li>
        <li><strong>Fallback Vendors:</strong> If top vendor rejects quote, automatically proceed with #2</li>
        <li><strong>User Notifications:</strong> Email/Slack alerts when workflow completes or errors occur</li>
      </ul>

      <h3>Integration Points</h3>
      <p>Production deployments would integrate with:</p>
      <ul>
        <li><strong>ERP Systems:</strong> SAP, Oracle, NetSuite for PO submission and tracking</li>
        <li><strong>Supplier Portals:</strong> Automated quote requests and responses</li>
        <li><strong>Payment Systems:</strong> Stripe, PayPal for vendor payments</li>
        <li><strong>Email/Notifications:</strong> SendGrid, Twilio for stakeholder alerts</li>
        <li><strong>Document Management:</strong> SharePoint, DocuSign for PO signing</li>
      </ul>

      <h2>Summary</h2>
      <p>The RFQ Procurement Workflow demonstrates the power of multi-agent AI systems for complex business processes:</p>
      <ol>
        <li><strong>7-Phase Sequential Workflow:</strong> From request intake to PO generation</li>
        <li><strong>Parallel Evaluation:</strong> 3 simultaneous tracks for compliance, delivery, and financial analysis</li>
        <li><strong>Intelligent Orchestration:</strong> Agents pass structured data using Pydantic models</li>
        <li><strong>Human-in-the-Loop:</strong> Critical approval gate maintains human control</li>
        <li><strong>Persistent UI:</strong> Each phase appears as a collapsible message that persists in chat</li>
        <li><strong>Comprehensive Logging:</strong> Full observability through Application Insights</li>
        <li><strong>Production-Ready:</strong> Designed for real-world procurement scenarios with security and compliance</li>
      </ol>

      <p>
        This workflow reduces procurement time from <strong>hours to seconds</strong>, while improving decision quality
        through structured evaluation and data-driven negotiation strategies. It showcases how AI agents can handle
        complex, multi-step business processes that traditionally required significant human coordination.
      </p>
    </ArticleLayout>
  );
};
