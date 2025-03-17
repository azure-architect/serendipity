In Stage 2 (Contextualize folder), the following happens:

1. The system retrieves the file from the Capture folder
2. Enrichment processes run to add context to the raw content:
   - Primary categorization is applied (work/personal/recovery/etc.)
   - Metadata tags are expanded based on content analysis
   - LLM performs initial scan to identify:
     - Key entities mentioned
     - Emotional tone/urgency signals
     - Potential connections to existing content
   - Timestamps for context (when captured, time of day patterns)
   - Brief summary generation (1-2 sentences)

3. The original content remains unchanged, but is now wrapped with a metadata layer that provides context for further processing

The Contextualize stage acts as a bridge between raw capture and deeper analysis. It doesn't alter the core content but enriches it with sufficient context so that later stages can process it more effectively. This contextual layer helps the system understand where this thought fits within your broader knowledge ecosystem.

The goal is to add just enough context to make the content processable while preserving its original meaning and intent. This sets up the content for more meaningful transformation in the following stages.

Would you like me to continue with Stage 3?