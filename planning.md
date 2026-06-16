# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): ...
- `size` (str): ...
- `max_price` (float): ...

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): ...
- `wardrobe` (dict): ...

**What it returns:**
<!-- Describe the return value -->

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (...): ...

**What it returns:**
<!-- Describe the return value -->

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | |
| suggest_outfit | Wardrobe is empty | |
| create_fit_card | Outfit input is missing or incomplete | |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1: Search for matching listings**

The agent extracts the search criteria from the user's request:

- Description: "vintage graphic tee"
- Maximum price: $30
- Size: not specified

The agent calls:

search_listings(
    description="vintage graphic tee",
    size=None,
    max_price=30.0
)

The tool searches the listings dataset and returns matching items sorted by relevance. The agent selects the highest-ranked result.

Example result:

{
  "title": "Faded Band Tee",
  "price": 22,
  "platform": "Depop",
  "condition": "Good",
  "size": "M"
}

If no listings are found, the agent informs the user and suggests adjusting the search criteria.

**Step 2: Generate an outfit suggestion**

The selected listing from Step 1 is stored in the agent's state and passed to the outfit tool along with the user's wardrobe information.

The agent calls:

suggest_outfit(
    new_item=<Faded Band Tee>,
    wardrobe=<user wardrobe>
)

The tool analyzes the new item and wardrobe pieces to generate styling recommendations.

Example result:

"Pair the faded band tee with your baggy jeans and chunky sneakers for a relaxed 90s-inspired look. Add a flannel overshirt for layering."

If the wardrobe is empty or has too few items, the tool provides a generic styling suggestion instead of failing and non availability in the wardrobe is implied in the result.

**Step 3: Create a shareable fit card**

The outfit recommendation and selected listing are passed to the final tool.

The agent calls:

create_fit_card(
    outfit=<outfit suggestion>,
    new_item=<Faded Band Tee>
)

The tool generates a short social-media-style caption describing the complete outfit.

Example result:

"Found this faded band tee for $22 on Depop and it fits perfectly with my baggy jeans and chunky sneakers 🔥 thrift finds never miss."

If the tool encounters an issue, the agent returns the outfit recommendation without the fit card rather than ending the workflow.

**Final output to user:**

Top Match:
- Faded Band Tee
- $22
- Depop
- Good condition

Outfit Suggestion:
Pair the faded band tee with your baggy jeans and chunky sneakers for a relaxed 90s-inspired look. Add a flannel overshirt for layering.

Fit Card:
"Found this faded band tee for $22 on Depop and it fits perfectly with my baggy jeans and chunky sneakers 🔥 thrift finds never miss."