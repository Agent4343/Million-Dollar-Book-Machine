"""
Content Mode System

Defines content modes that reshape how every agent generates output.
Each mode provides instruction overlays that are injected into agent
prompts, transforming the system from a fiction/non-fiction book engine
into a course builder, workbook generator, etc.

Currently supported modes:
- "book" (default): Standard book generation
- "teaching": Instructional course content
"""

from typing import Dict, Any, Optional


# ─────────────────────────────────────────────────────────────────────
# Mode definitions
# ─────────────────────────────────────────────────────────────────────

VALID_MODES = {"book", "teaching"}
DEFAULT_MODE = "book"


def get_mode(user_constraints: Optional[Dict[str, Any]]) -> str:
    """Extract the content mode from user constraints."""
    if not user_constraints or not isinstance(user_constraints, dict):
        return DEFAULT_MODE
    mode = user_constraints.get("content_mode", DEFAULT_MODE)
    return mode if mode in VALID_MODES else DEFAULT_MODE


def is_teaching_mode(user_constraints: Optional[Dict[str, Any]]) -> bool:
    """Check if the project is in teaching/course mode."""
    return get_mode(user_constraints) == "teaching"


# ─────────────────────────────────────────────────────────────────────
# Per-agent teaching-mode instruction overlays
#
# Each key maps to an agent_id.  The value is a block of text that
# gets injected into that agent's prompt when teaching mode is active.
# ─────────────────────────────────────────────────────────────────────

_TEACHING_OVERLAYS: Dict[str, str] = {

    # ── Layer 1: Market Intelligence ──
    "market_intelligence": """
## MODE: TEACHING / COURSE CONTENT
You are analyzing the market for an INSTRUCTIONAL PRODUCT, not a book for passive reading.

Reframe your analysis:
- **Reader Avatar** → **Student Avatar**: Who is learning this? What skill level are they starting at?
  What have they already tried and failed at? What does "success" look like for them?
- **Market Gap** → **Learning Gap**: What existing courses/books fail to teach? Where do students
  get stuck? What's the gap between theory and practice in this space?
- **Positioning Angle** → **Teaching Angle**: What makes THIS course different? Is it the method,
  the teacher's credibility, the step-by-step framework, or the results students can expect?
- **Comp Analysis** → **Competing Learning Resources**: Analyze courses, workshops, YouTube channels,
  and books that teach similar material. What do they skip? Where do students drop off?

Additional output fields to include:
- "student_starting_point": Where students typically are when they start
- "student_end_goal": What they can DO after completing this course
- "common_failure_points": Where most self-learners get stuck without guidance
""",

    # ── Layer 2: Concept Definition ──
    "concept_definition": """
## MODE: TEACHING / COURSE CONTENT
You are defining the core concept for an INSTRUCTIONAL COURSE, not a narrative book.

Reframe your output:
- **One-Line Hook** → **Course Promise**: A single sentence that tells the student exactly what
  they will be able to DO after completing this. Not vague ("learn marketing") but specific
  ("launch your first paid ad campaign that generates leads within 7 days").
- **Core Promise** → **Transformation Promise**: Be brutally specific about the before/after.
  What can't they do now? What will they be able to do? How will their daily life change?
- **Unique Engine** → **Teaching Method**: What's the specific methodology? A framework?
  A step-by-step system? Name it. ("The 4-Layer Launch Method", "The Reverse Outline System")
- **Elevator Pitch** → **Course Pitch**: Sell the transformation, not the content.
  "In 6 modules, you'll go from [starting point] to [end result] using [method name]."

The one-line hook MUST pass this test: if a student reads it, they should think
"That's exactly what I need" within 3 seconds.
""",

    # ── Layer 3: Thematic Architecture ──
    "thematic_architecture": """
## MODE: TEACHING / COURSE CONTENT
You are designing the LEARNING ARCHITECTURE, not a thematic arc.

Reframe your output:
- **Primary Theme** → **Core Skill**: The one skill this course is really teaching, even if it
  covers many topics. Everything connects back to this.
- **Secondary Themes** → **Supporting Skills**: Complementary abilities the student develops
  along the way. These are the "oh, I didn't realize I'd also learn THIS" moments.
- **Thematic Argument** → **Teaching Philosophy**: What does this course believe about how people
  learn best? (e.g., "You learn by doing, not by watching" or "Master the fundamentals before
  any advanced technique"). This philosophy should drive every module's design.
- **Motifs** → **Recurring Frameworks**: Mental models, checklists, or frameworks that
  reappear across modules, building familiarity and confidence through repetition.

Include a "learning_progression" field showing the skill-building ladder:
  Module 1 skill → Module 2 builds on it → ... → Final module integrates everything.
""",

    # ── Layer 4: Story Question ──
    "story_question": """
## MODE: TEACHING / COURSE CONTENT
You are defining the CENTRAL LEARNING QUESTION, not a dramatic question.

Reframe your output:
- **Central Dramatic Question** → **Central Learning Question**: The question the student is
  trying to answer. Frame it as: "Can I actually [achieve specific outcome]?"
  e.g., "Can I actually write a novel in 90 days?" or "Can I build a profitable side business?"
- **Stakes** → **Student Stakes**: What happens if they DON'T learn this? What opportunities
  do they miss? What pain continues? Make the cost of inaction concrete.
- **Question Engine** → **Motivation Engine**: What keeps the student engaged module after module?
  Quick wins? Progress tracking? Community? Real-world results they can see?

Include:
- "quick_win_promise": What the student achieves in the FIRST module/session to build momentum
- "halfway_milestone": A tangible result they'll have by the midpoint of the course
""",

    # ── Layer 5: World / Context Rules ──
    "world_rules": """
## MODE: TEACHING / COURSE CONTENT
You are defining the LEARNING ENVIRONMENT AND PREREQUISITES, not a fictional world.

Reframe your output:
- **World Rules** → **Course Prerequisites & Environment**:
  - What tools/software/materials does the student need?
  - What knowledge level is assumed?
  - What environment should they set up before starting?
- **Tone Rules** → **Learning Culture**: Is this a "no judgment, everyone starts somewhere"
  environment? A "push yourself hard" bootcamp? A "go at your own pace" self-study?
- **World Logic** → **Domain Principles**: The fundamental truths of this subject matter that
  the student needs to internalize. (e.g., in writing: "Show don't tell"; in business:
  "Revenue solves most problems")

Include:
- "tools_needed": List of specific tools, software, or materials
- "time_commitment": Realistic hours per module/week
- "setup_checklist": What to do before Module 1
""",

    # ── Layer 6: Character Architecture ──
    "character_architecture": """
## MODE: TEACHING / COURSE CONTENT
You are designing the STUDENT JOURNEY AND INSTRUCTOR PERSONA, not fictional characters.

Reframe your output:
- **Protagonist Profile** → **Student Persona**: The typical student taking this course.
  Their current frustrations, skill level, time constraints, and what has NOT worked for them.
- **Protagonist Arc** → **Student Transformation Arc**: Where they start → the "aha moment" in
  the middle → where they end up. Map this to specific modules.
- **Want vs Need** → **What Students THINK They Need vs What They ACTUALLY Need**: Students
  often come wanting shortcuts but actually need foundations. Name this gap explicitly.
- **Antagonist Profile** → **Resistance & Obstacles**: What internal resistance will students face?
  (Imposter syndrome, perfectionism, overwhelm, "I don't have time", "This won't work for me")
- **Supporting Cast** → **Teaching Archetypes**:
  - The Instructor persona (mentor tone, credibility, teaching style)
  - Guest Expert voices (if applicable)
  - Student Success Stories (case studies to include)
  - The Inner Critic (the voice in the student's head the course must counter)

Skip "dialogue_voices" — replace with "instructor_voice":
  - How the instructor speaks (casual? authoritative? encouraging?)
  - Phrases the instructor uses ("Here's what most people miss...", "Let me show you...")
  - How the instructor handles student doubt
""",

    # ── Layer 7: Relationship Dynamics ──
    "relationship_dynamics": """
## MODE: TEACHING / COURSE CONTENT
You are designing the STUDENT-CONTENT RELATIONSHIP, not character relationships.

Reframe:
- **Relationships** → **Engagement Dynamics**:
  - Student ↔ Instructor: Trust-building progression (skeptic → believer → practitioner)
  - Student ↔ Material: Difficulty curve (easy wins → challenge → mastery)
  - Student ↔ Community: If applicable, how peer interaction enhances learning
  - Student ↔ Self: How their self-image evolves (impostor → competent → confident)
""",

    # ── Layer 8: Plot Structure ──
    "plot_structure": """
## MODE: TEACHING / COURSE CONTENT
You are designing the COURSE STRUCTURE / CURRICULUM, not a plot.

Reframe your output:
- **Three-Act Structure** → **Three-Phase Curriculum**:
  - Phase 1 (Foundation): Core concepts, mindset shifts, quick wins. Student thinks: "I can do this!"
  - Phase 2 (Development): Deep skill-building, practice exercises, real projects. Student thinks: "This is hard but I'm growing."
  - Phase 3 (Mastery): Integration, advanced techniques, launch/completion. Student thinks: "I did it."
- **Plot Points** → **Key Learning Milestones**: Specific achievements that mark progress
- **Conflict** → **Challenges / Exercises**: Points where the student must DO something hard
- **Resolution** → **Capstone Project**: The final deliverable that proves mastery

Each "chapter" = one MODULE with:
  - A clear learning objective (what can the student DO after this module?)
  - A concept lesson (the "why")
  - A walkthrough (the "how")
  - A practice exercise (the "do")
  - Common mistakes section (the "watch out")
  - Homework/action item (the "now go apply it")
""",

    # ── Layer 9: Pacing Design ──
    "pacing_design": """
## MODE: TEACHING / COURSE CONTENT
You are designing LEARNING PACING, not narrative tension.

Reframe:
- **Tension Curve** → **Difficulty Curve**: How challenge increases across modules. Include
  "breather" modules after hard ones. Never stack two hard modules back-to-back.
- **Pacing Beats** → **Energy Management**:
  - After heavy theory → practice exercise (active)
  - After difficult exercise → success story / motivation (recovery)
  - Before a hard module → quick win in current module (confidence boost)
- **Scene Types** → **Content Types**: Alternate between:
  - Concept lessons (theory)
  - Step-by-step walkthroughs (demonstration)
  - Practice exercises (doing)
  - Case studies (inspiration)
  - Templates/scripts (tools)
  - Q&A / troubleshooting (support)

Include Module 1 pacing note: Module 1 MUST include a quick-win exercise that the student
can complete in under 30 minutes and get a tangible result. This is non-negotiable — it
creates the momentum that carries them through the harder modules.
""",

    # ── Layer 10: Chapter Blueprint ──
    "chapter_blueprint": """
## MODE: TEACHING / COURSE CONTENT
You are designing MODULE BLUEPRINTS, not chapter outlines.

Each "chapter" is a MODULE. Structure each module as:

1. **Module Opening** (replaces "opening hook"):
   - The problem this module solves, stated in the student's own language
   - "By the end of this module, you will be able to: [specific action]"
   - WHY this matters (real-world consequence of not knowing this)

2. **Concept Section** ("the WHY"):
   - Core principle explained with an analogy or story
   - Common misconception debunked
   - Framework or mental model introduced

3. **Walkthrough Section** ("the HOW"):
   - Step-by-step demonstration with the instructor narrating decisions
   - "Here's what I'm doing and WHY I'm doing it this way..."
   - Screenshots/examples described (the student will reference these)

4. **Practice Section** ("the DO"):
   - Exercise with clear instructions
   - Expected output described ("When you're done, you should have...")
   - Time estimate for the exercise
   - Stretch goal for advanced students

5. **Common Mistakes** ("the WATCH OUT"):
   - 3-5 specific mistakes students make at this point
   - WHY each mistake happens (not just "don't do this")
   - How to recognize and fix each one

6. **Module Closing** (replaces "closing hook"):
   - Recap: "In this module, you learned to..."
   - Homework/action item with deadline suggestion
   - Preview of next module: "Now that you can [X], we'll use that to [Y]..."

7. **Templates/Scripts** (NEW):
   - Copy-and-customize templates relevant to this module
   - Checklists, scripts, frameworks the student can use immediately

For MODULE 1 specifically:
- Include a QUICK-WIN exercise that takes <30 minutes
- The exercise should produce something the student can show someone
- This creates immediate proof that the course works, building momentum

Word targets per module should be based on content density, not arbitrary counts.
Walkthrough-heavy modules will be longer. Concept-focused modules shorter.
""",

    # ── Layer 11: Voice Specification ──
    "voice_specification": """
## MODE: TEACHING / COURSE CONTENT
You are specifying the INSTRUCTOR VOICE, not a narrator's literary voice.

Reframe your output:
- **Narrative Voice** → **Instructor Voice**:
  - POV: Second person ("you") — direct address to the student
  - Distance: Close and personal. The instructor is sitting across the table.
  - Personality: Mentor who has done this themselves. Shares real stories, not theory.
  - Tone: Encouraging but direct. Like a coach who believes in the student but won't
    sugarcoat the hard parts. "This step is hard. Most people skip it. Don't."

- **Tense Rules** → **Tense Approach**:
  - Present tense for instructions ("Open the file. Click settings.")
  - Past tense for instructor stories ("When I first tried this, I failed spectacularly.")
  - Future tense for student outcomes ("After this module, you'll be able to...")

- **Dialogue Style** → **Instructor Speech Patterns**:
  - Uses rhetorical questions to create engagement ("Sound familiar?")
  - Breaks the fourth wall regularly ("I know what you're thinking...")
  - Includes asides that build trust ("Between us, most 'gurus' skip this step too.")
  - Validates difficulty ("If this feels hard, good — it means you're actually learning, not just reading.")

- **Style Guide** → **Teaching Style Guide**:
  - DO: Use concrete examples, real numbers, specific tools, named strategies
  - DO: Include "coach's note" sidebars for important context
  - DO: Use transitions like "Now that you've [done X], let's..."
  - DON'T: Use vague motivational language ("believe in yourself!")
  - DON'T: Use academic language or jargon without defining it first
  - DON'T: Tell the student something is "easy" — instead say "straightforward once you see the pattern"
  - Example passage: "Here's where most people overcomplicate things. You don't need a perfect plan.
    You need a working plan. Open a blank document and write three lines: what you're selling,
    who it's for, and why they should care. That's it. We'll refine later. Just get it down."
""",

    # ── Layer 12: Draft Generation ──
    "draft_generation": """
## MODE: TEACHING / COURSE CONTENT
You are writing INSTRUCTIONAL MODULE CONTENT, not narrative prose.

CRITICAL RULES FOR TEACHING CONTENT:
1. Address the student directly as "you" throughout
2. Structure every module following the blueprint: Opening → Concept → Walkthrough → Practice → Mistakes → Closing → Templates
3. The instructor voice is a mentor who has done this — use first person for stories ("When I first...")
4. Show the student's inner doubts and address them directly ("You might be thinking 'but what if...'")
5. Every concept MUST have a concrete example. No theory without application.
6. Step-by-step walkthroughs use numbered steps with WHY explanations:
   "Step 1: Open your analytics dashboard.
    Why this matters: You can't improve what you can't measure. Most people skip this
    and end up guessing — which is why most people fail."
7. Practice exercises must have:
   - Clear instructions (what to do)
   - Expected output (what success looks like)
   - Time estimate ("This should take 15-20 minutes")
   - A "stuck?" section with hints
8. Common mistakes sections are GOLD — be specific and empathetic:
   "Mistake #2: Trying to make it perfect before shipping.
    Why this happens: Your brain is protecting you from judgment. It disguises fear as 'quality standards.'
    The fix: Set a timer for 30 minutes. When it rings, ship what you have. You can always iterate."
9. End every module with specific homework:
   "Your homework: [Specific task]. Deadline: Before you start Module [N+1].
    Why this matters: [Consequence of skipping]."
10. Include copy-and-customize templates where relevant:
    "Here's a template you can steal: [template]
     Customize the [bracketed parts] for your situation."

PROSE RULES (adapted for teaching):
- Short paragraphs (2-4 sentences). Students skim. Make every paragraph earn its place.
- Use bold for key terms when first introduced
- Use bullet points for lists of 3+ items
- Use numbered steps for sequential instructions
- Include "Coach's Note:" callouts for important asides
- Vary energy: concept explanation (calm) → exercise instructions (direct) → encouragement (warm)

DO NOT write like an academic textbook. Write like a smart friend explaining something
over coffee — clear, specific, occasionally funny, and always actionable.
""",

    # ── Layers 13+: Validation & Editing ──
    "continuity_audit": """
## MODE: TEACHING / COURSE CONTENT
Audit for INSTRUCTIONAL CONTINUITY, not narrative continuity:
- Do concepts build on each other in the right order? (No reference to undefined terms)
- Are prerequisites taught before they're needed?
- Do homework assignments use skills from the current module, not future ones?
- Is the difficulty progression consistent? (No sudden jumps)
- Do "success stories" and examples stay consistent across modules?
- Are promised templates/scripts actually provided?
""",

    "emotional_validation": """
## MODE: TEACHING / COURSE CONTENT
Validate STUDENT MOTIVATION AND ENGAGEMENT, not emotional impact:
- Does Module 1 deliver a quick win? (Non-negotiable)
- Are there motivation dips between modules? Add success stories or encouragement.
- Does each module answer "why should I care about this?"
- Are the hardest modules preceded by confidence-boosting exercises?
- Is there a clear "halfway milestone" the student can celebrate?
- Does the final module feel like a genuine achievement, not just an ending?
""",

    "developmental_editor": """
## MODE: TEACHING / COURSE CONTENT
Evaluate as an INSTRUCTIONAL DESIGNER, not a fiction editor:

Priority order for teaching content:
1. **Learning Progression**: Does each module build on the previous? Any gaps?
2. **Clarity**: Can a student follow every instruction without guessing?
3. **Practice Ratio**: Is there enough "doing" vs "reading"? (Target: 40%+ exercises)
4. **Quick Win Check**: Does Module 1 deliver a tangible result in <30 minutes?
5. **Template Coverage**: Does every applicable module include copy-and-customize templates?
6. **Stuck Points**: Are common failure points addressed proactively?
7. **Homework Quality**: Is every homework assignment specific, achievable, and meaningful?
8. **Motivation Architecture**: Does the student have reasons to keep going at every stage?
""",

    "structural_rewrite": """
## MODE: TEACHING / COURSE CONTENT
Rewrite for INSTRUCTIONAL QUALITY, not narrative prose:
- Replace vague instructions with specific step-by-step actions
- Add concrete examples where concepts are explained abstractly
- Ensure every module has: concept → walkthrough → exercise → homework
- Add "Common Mistakes" sections where missing
- Add "Coach's Note" callouts for important context
- Ensure templates are copy-ready (not placeholder text)
- Fix any jargon used without definition
- Verify exercise instructions are unambiguous
""",

    "line_edit": """
## MODE: TEACHING / COURSE CONTENT
Edit for INSTRUCTIONAL CLARITY, not literary style:
- Simplify complex sentences — teaching content must be scannable
- Ensure consistent formatting (all steps numbered, all lists bulleted)
- Check that bold is used for key terms at first introduction
- Verify "you" is used consistently (not switching between "you", "one", "we")
- Tighten exercise instructions — remove any ambiguity
- Ensure module transitions are smooth ("Now that you can X, let's use that to Y")
""",

    "publishing_package": """
## MODE: TEACHING / COURSE CONTENT
Create a COURSE PUBLISHING PACKAGE, not a book publishing package:
- **Course Title**: Clear, benefit-driven (e.g., "Write Your Novel in 90 Days")
- **Course Subtitle**: Method + result (e.g., "The Step-by-Step System for First-Time Authors")
- **Course Description**: Sell the transformation, not the content. Use student language.
- **Module List**: Clean list of all modules with one-line descriptions
- **Prerequisites**: What students need before starting
- **Learning Outcomes**: 5-7 specific things students can DO after completing the course
- **Target Student**: Who this is for (and who it's NOT for)
- **Keywords**: Course-related search terms for discoverability
""",
}


# ─────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────

def get_teaching_overlay(agent_id: str) -> str:
    """Return the teaching-mode overlay for a given agent, or empty string."""
    return _TEACHING_OVERLAYS.get(agent_id, "")


def build_mode_instructions(agent_id: str, user_constraints: Optional[Dict[str, Any]]) -> str:
    """Build mode-specific instruction text to inject into an agent prompt.

    Returns an empty string for default book mode, or a teaching-mode
    instruction block for teaching mode.  The caller should append this
    to the prompt.
    """
    if not is_teaching_mode(user_constraints):
        return ""
    overlay = get_teaching_overlay(agent_id)
    if not overlay:
        # Generic fallback for agents without a specific overlay
        return """
## MODE: TEACHING / COURSE CONTENT
Adapt your output for instructional course content. Instead of narrative book content,
generate material suitable for teaching a student how to DO this process themselves.
Use second person ("you"), include step-by-step instructions, explain WHY each step matters,
and include actionable homework at the end.
"""
    return overlay
