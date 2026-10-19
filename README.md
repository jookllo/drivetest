# DriveTest — quiz website, colours, and mascot guide

Last updated: 19 October 2026.

DriveTest is a road-sign learning project for a public quiz website and a future mobile app. Players should be able to practise without creating an account, receive useful explanations, and share their scores. The owner needs a private editor for signs, questions, answers, and publication.

This README records the product direction, proposed colour system, mascot assets, content requirements, and implementation priorities. It is a handoff guide for future design and development work. **A requirement documented here is not a claim that the feature has already been built.**

### Start here

- [Run the server, use the API, and import labels](#14-api-setup-endpoints-and-content-operations)
- [Try the local demo](#local-demo-when-no-public-questions-are-available)
- [Current implementation and correction plan](#1-current-state-and-agreed-direction)
- [Colours](#2-colour-palette) and [mascot files](#4-where-the-mascot-files-are)
- [Question bank requirements](#7-question-bank-and-owner-provided-content)
- [SVG library and label editing](#15-svg-library-and-label-editing-workflow)
- [Which document to maintain](#16-documentation-ownership)
- [Quiz combinations and timing](#17-quiz-generation-length-and-timing)
- [Exact implementation folders and theme](#18-implementation-map-and-theme-contract)
- [Printed and handwritten question intake](#19-importing-typed-and-handwritten-questions)

## 1. Current state and agreed direction

| Area | Current state / direction |
| --- | --- |
| Sign library | Existing SVG artwork, names, label files, and browser-based label tools. Artwork and classifications still require review before public use. |
| Backend | Existing Laravel API and MySQL setup, with read endpoints and a CLI sign importer. See section 14 below for setup and endpoints. |
| Public quiz | A Vue 3 frontend is served by the Laravel app at `/quiz` (no build step: a vendored global Vue build plus plain CSS/JS in `api/public/`). It consumes stored questions and server-selected, server-marked guest attempts. |
| Quiz scope | Expand to sign meanings, classes, subcategories, general road questions, multiple-choice questions, and questions with multiple correct answers. |
| Player accounts | Not required for the initial website. |
| Quiz generation and timers | Implemented: 10/20-question practice and a 10-question, 5-minute challenge with server deadlines. The isolated local demo stays at four samples. |
| Administration | Protected sign and question editor at `/mdosimimi`, with terminal account creation and password recovery. |
| Results and sharing | Server-marked scores and opaque, shareable result links are implemented. |
| Colours | Forest green, warm cream, charcoal, white, amber, and burgundy are the proposed visual direction recorded below. |
| Mascot | Blanket-and-drink image is wired into the Vue results page. Hands-on-cheeks sharing pose remains on a concept sheet and is not integrated. |

This is the single maintained project guide. The previous API README, sign-library README, and API design document have been consolidated here and removed. Coding-agent implementation rules remain in [api/AGENTS.md](api/AGENTS.md); they must not define a competing product specification. Third-party dependency documentation is outside this consolidation.

### Public quiz frontend

The current quiz is a Vue 3 single-page prototype served by Laravel. It uses a vendored global Vue build in `api/public/vendor/vue.global.prod.js`; its own code does not require a bundler. The implementation is in [app.js](api/public/assets/quiz/app.js), [quiz.css](api/public/assets/quiz/quiz.css), and the [Blade page shell](api/resources/views/quiz.blade.php).

Start Laravel on the project’s API port, if it is not already running:

```bash
cd /home/okello/Documents/projects/DriveTest/api
php artisan serve --host=127.0.0.1 --port=8001
```

Open `http://127.0.0.1:8001/quiz`; `/` on that server serves the same page. The separate root `index.html` redirects to the old labeling tool. Serving the repository with a static server on port 8000 does not run Laravel or its API.

- The connected page reads the stored question bank through session-protected quiz endpoints. Both single- and multiple-answer questions can be authored for each topic.
- The proposed palette is already used by the stylesheet. Reusing the existing Vue shell and CSS is reasonable; switching frameworks will not solve the missing quiz model.
- During review on 18 October, the live page showed “No published signs are available yet.” No records were published or edited during the review.
- The CLI `signs:publish` command exists, but changing publication status does not verify artwork, classification, or question quality. Do not bulk-publish the catalog merely to make the demo work. Use a reviewed, explicitly selected set for public content; use isolated sample data for prototype testing.

### Local demo when no public questions are available

In local development on this computer, open `http://127.0.0.1:8001/quiz?demo=1`, or choose **Try the local demo** on the unavailable screen. This runs four explicit sample questions: sign identification, class, subcategory, and multiple-answer selection. It does not access the database, publish signs, save scores, or generate share links. It is enabled only for `APP_ENV=local` and loopback requests; production does not receive the fixture data.

The samples live in `api/resources/quiz-demo.json` and are for interface testing only. They are separate from the implemented database question bank and admin editor. The main public quiz still requires published catalog content.

### Current implementation and administration

The 18 October review found client-side scoring, missing authoring and lost progress. The connected quiz now uses a stored question bank and server-marked guest attempts. The four-question local demo remains deliberately separate.

Open `/mdosimimi` on the Laravel server to sign in to the private editor. `/admin` returns 404. The protected API continues to use `/api/v1/admin/*`; the custom page address is a convenience, not an authentication control.

Create an administrator from the server terminal:

```bash
cd api
php artisan app:create-admin your-email@example.com
```

The command asks for a password privately. If you forget it, run:

```bash
php artisan app:reset-admin-password your-email@example.com
```

Recovery requires server/terminal access, an existing administrator email, and matching passwords of at least 12 characters. It rotates the remember token and removes that administrator's database sessions. Protected admin requests also use Laravel's password/session check. Never put the password in command arguments, chat, or Git. Email reset links are **not implemented**: they require a configured transactional mail service and a throttled, expiring token flow. No public registration or default production password exists.

The editor supports sign labels/classification, question wording, 2–6 options, single or multiple correct answers, explanations, optional sign links, ordered groups, source notes, drafts and reviewed publication. Question updates check a version number; sign updates check the last modification timestamp. Editing sign content returns affected questions to draft. Editing existing questions does not change the answer key frozen in an existing attempt.

### Guest sessions, scoring and timing

- Players do not log in. A random secret in their cookie-backed Laravel session owns attempts; the database stores its hash. Another browser cannot access private attempts just by knowing their IDs.
- Reloading an attempt URL restores **saved** answers while the session remains valid. Practice answers save on **Check answer**; challenge choices save immediately. Unchecked practice choices are not saved. Clearing cookies, expiry, or signing out of the editor ends access to that session's private progress.
- Session lifetime is configured by `SESSION_LIFETIME` (default 120 minutes of inactivity). Practice attempts have a 24-hour server deadline; challenges have a five-minute deadline and ten questions. The shorter session lifetime can end access before an attempt deadline.
- Practice supports 10 or 20 questions. Mixed quizzes use topic quotas, unique independent signs and complete ordered groups. Selection fails clearly if reviewed content cannot satisfy the requested mix; it does not silently publish drafts or shorten the quiz.
- Answers and question text are snapshotted per attempt. Correct answers remain private until practice feedback is due or the attempt ends. Related groups defer feedback until the group is answered. Multiple-answer marking requires the exact set, with one point per question.
- The server enforces deadlines, locks practice answers, permits challenge revisions before expiry and finalises idempotently. `/results/{publicId}` shares a stored score summary, never the session secret or private answer history.
- Image URLs reference the catalog, not immutable artwork copies. Withdrawing an image can make it unavailable in an older review. Immutable image versioning remains future work.

### Connected endpoints and implementation files

Quiz/session routes live in `api/routes/quiz.php`, loaded from `routes/web.php` so mutations receive session and CSRF protection. Catalog reads remain in `routes/api.php`.

| Method and path | Purpose |
| --- | --- |
| GET `/api/v1/quiz-session` | Guest session bootstrap, CSRF token and latest attempt |
| GET `/api/v1/quiz-topics` | Eligible question counts and classification filters |
| POST `/api/v1/quiz-attempts` | Start with topic, mode, length and optional filters |
| GET `/api/v1/quiz-attempts/{id}` | Resume owned attempt |
| POST `/api/v1/quiz-attempts/{id}/answers` | Save question ID and selected option IDs |
| POST `/api/v1/quiz-attempts/{id}/complete` | Finalise owned attempt |
| GET `/api/v1/results/{publicId}` | Public final score summary |
| GET `/api/v1/admin/session` | Admin state and CSRF bootstrap |
| POST `/api/v1/admin/login`, `/logout` | Administrator sign-in/out |
| GET, POST `/api/v1/admin/questions` | List or create questions |
| PUT `/api/v1/admin/questions/{id}` | Validate and update a question |
| GET `/api/v1/admin/signs` | Private sign catalog |
| PUT `/api/v1/admin/signs/{id}` | Review and update a sign |
| GET `/api/v1/admin/signs/{id}/image` | Protected artwork preview |

For session APIs, retain cookies and send the bootstrap token as `X-CSRF-TOKEN` on writes, with `Accept: application/json`. Browser authentication uses Laravel sessions and admin authorization; Sanctum is not installed. Mobile authentication is a future decision.

Core implementation: `app/Services/QuizEngine.php`, `app/Models/Question.php`, `app/Models/QuizAttempt.php`, `app/Http/Controllers/Api/`, `config/quiz.php`, and the quiz migration, all under `api/`. The editor UI is `api/public/assets/quiz/admin.js`; the player is `app.js` in that same folder, with shared `quiz.css`.

### Content operations and launch work

Run `php artisan migrate` from `api/` after pulling. `php artisan db:seed --class=StarterQuestionSeeder` adds taxonomy **drafts**, not an approved public bank. Review artwork and questions in the editor before publication. An empty reviewed bank correctly shows no available questions.

Import up to 500 questions from a JSON array with `php artisan questions:import /path/to/questions.json --dry-run`, then repeat without `--dry-run`. Each object uses the editor fields: `prompt`, `topic`, `type`, `options` (objects with `id` and `label`), `correct_ids`, `explanation`, optional `sign_id`, `class_code`, `subcategory_id`, `group_key`, `group_order`, `shuffle_options`, and `source_notes`. All imported questions become drafts; invalid batches and duplicate prompts are rejected atomically. Record typed and handwritten transcription uncertainty in source notes; do not guess unclear answer keys.

Run `php artisan test --compact` from `api/`. PHPUnit pins MySQL to `drivetest_test`, which must exist separately from `drivetest`. `QuizBrowserSeeder` is restricted to that test database and contains disposable fixture credentials; never use it for real content.

Named throttles, restrictive default CORS, admin authorization, CSRF, private response caching, production debug suppression, HTTPS redirects and secure-cookie defaults are implemented. Before deployment configure `APP_ENV=production`, `APP_DEBUG=false`, `APP_URL=https://your-domain`, `SESSION_SECURE_COOKIE=true`, a real TLS certificate and only your reverse proxy addresses in `TRUSTED_PROXIES`. Keep CORS origins empty for same-origin use; explicitly configure `CORS_ALLOWED_ORIGINS` if needed. Serve only `api/public`, never the repository root. Run Laravel's scheduler every minute for `quiz:expire`; reads/submissions also enforce expiry.

Remaining launch work: reviewed question coverage, sign/artwork verification, the standalone sharing mascot, comprehensive device/accessibility checks, mail-based recovery if wanted, hosting/TLS, backups and restore drills, monitoring, and an anonymous-data retention/deletion policy. Per-question timers, adaptive selection and mobile tokens are not implemented. Theme and mascot requirements below remain the design contract.

## 2. Colour palette

The website should feel warm, clear, and encouraging. Road signs are the learning content, so their colours must remain easy to distinguish from the interface.

| Name | Hex | Primary use | Avoid |
| --- | --- | --- | --- |
| Forest green | `#215B46` | Main actions, selected choices, links, navigation accents, progress fill | Large decorative areas that compete with the question |
| Warm cream | `#F7F4EC` | Main page background and quiet surrounding space | Applying a tint to the sign artwork itself |
| White | `#FFFFFF` | Question cards, sign display panels, text on green buttons | White text on amber |
| Asphalt charcoal | `#252A28` | Headings, body text, labels, text on amber | Low-opacity essential instructions |
| Road amber | `#E7AD35` | Small progress milestones, highlights, attention cues | Default body text, every button, or an automatic indication of a wrong answer |
| Burgundy | `#8B263B` | Small brand accents that relate to the mascot's hair | Using it everywhere or making it the only way to identify an error |

### Visual balance

- Make cream and white the dominant surfaces.
- Use charcoal for reading and green for the primary action on each screen.
- Use amber sparingly; road signs already introduce strong red, blue, and yellow.
- Let the mascot supply much of the burgundy. Not every component needs another accent.
- Keep a sign's original colours and proportions. Put it on a clean white panel without filters, recolouring, or decorative gradients behind its face.
- Do not infer a sign's class from its colour. Some blue signs are facilities; the database classification determines the answer.

### Suggested CSS tokens

These are the baseline tokens already reflected in `api/public/assets/quiz/quiz.css`. Continue using them when correcting the quiz; verify added states separately.

```css
:root {
  --dt-color-green: #215b46;
  --dt-color-cream: #f7f4ec;
  --dt-color-white: #ffffff;
  --dt-color-charcoal: #252a28;
  --dt-color-amber: #e7ad35;
  --dt-color-burgundy: #8b263b;

  --dt-page-bg: var(--dt-color-cream);
  --dt-card-bg: var(--dt-color-white);
  --dt-text: var(--dt-color-charcoal);
  --dt-action-bg: var(--dt-color-green);
  --dt-action-text: var(--dt-color-white);
  --dt-selected-border: var(--dt-color-green);
  --dt-highlight-bg: var(--dt-color-amber);
  --dt-highlight-text: var(--dt-color-charcoal);
}
```

### Contrast and accessibility

The following contrast ratios were calculated from the exact solid hex colours above. They do not cover image backgrounds, opacity, gradients, or every interaction state.

| Foreground / background | Approximate ratio | Intended use |
| --- | --- | --- |
| Charcoal / cream | 13.26:1 | Main reading text |
| White / green | 7.93:1 | Primary button text |
| Charcoal / amber | 7.24:1 | Highlight labels |
| Green / cream | 7.21:1 | Links and short labels |
| Burgundy / cream | 7.84:1 | Occasional accent text |
| White / amber | 2.01:1 | Do not use for normal text |

Use 4.5:1 as the minimum design target for normal text. Check borders, focus indicators, hover states, disabled states, and error states separately. These sample calculations are not a complete accessibility audit.

Always pair colour with words or symbols:

- Selected answer: visible selection indicator plus a border; selection is not yet correctness.
- Correct answer: green treatment with “Correct” and a check mark.
- Incorrect answer: a readable error treatment with “Incorrect” or “Not quite” and an explanation. Choose and validate a dedicated error-red token during implementation.
- Multiple answers: use checkboxes and the instruction “Select all that apply.”
- Links: use an underline or another non-colour cue.
- Focus: keep a clearly visible keyboard focus indicator.

The initial palette describes a light interface. A dark theme needs its own tested surfaces and contrast pairs; do not simply invert the artwork or reuse every light-theme value.

## 3. Mascot identity

The mascot is an original generated concept for a feminine, warm road companion. She does not yet have an approved name.

Recognisable features:

- A charcoal road-inspired body with cream lane markings.
- Burgundy flowing hair and expressive cartoon eyes.
- A welcoming expression and rounded, bold outlines.
- White cartoon gloves.
- Cream sneakers with green accents.
- A playful vintage cartoon style with simple, readable shapes.

Her role is to encourage learning and make the quiz feel approachable. She must never obscure a sign, answer option, score, or action button.

### Character direction to preserve

Keep poses relaxed, modest, friendly, and suitable for an educational site. The owner found the earlier rear-facing seated pose too risqué. Do not reuse that pose or emphasise the character's hips, rear, or body shape in future assets.

The preferred results pose has her sitting in an armchair with a drink and a cream-and-green checked blanket over her lap and legs, looking toward the results. Future revisions should preserve that welcoming tone.

## 4. Where the mascot files are

Project folder: [`assets/mascot/`](assets/mascot/).

Absolute location on this computer:

```text
/home/okello/Documents/projects/DriveTest/assets/mascot/
```

These repository copies are the stable handoff masters. A copy of the blanket results asset is already used by the Vue frontend at `api/public/assets/mascot/drivetest-results-blanket-v1.png`. The remaining poses are not integrated.

| File | Dimensions | Contents | Status / intended use |
| --- | --- | --- | --- |
| [drivetest-results-blanket-v1.png](assets/mascot/drivetest-results-blanket-v1.png) | 1306 × 1205 | Single mascot in an armchair, holding a drink, blanket over legs | Preferred results-page concept |
| [drivetest-welcome-concept-sheet-v1.png](assets/mascot/drivetest-welcome-concept-sheet-v1.png) | 1536 × 1024 | Two standing poses: waving and gesturing | Exploration for welcome and quiz guidance; not two separate assets yet |
| [drivetest-seated-concept-sheet-v1.png](assets/mascot/drivetest-seated-concept-sheet-v1.png) | 1536 × 1024 | Left: rear-facing drink pose. Right: hands cupping cheeks, seated with crossed legs | Use only the right-hand concept for sharing. Left pose is superseded and must not ship |
| [drivetest-results-no-blanket-v1.png](assets/mascot/drivetest-results-no-blanket-v1.png) | 1305 × 1205 | Armchair and drink without blanket | Historical reference; superseded by blanket version |

### Preferred results mascot

![Preferred DriveTest mascot seated in an armchair with a drink and a checked blanket over her legs](assets/mascot/drivetest-results-blanket-v1.png)

### Provenance and originals

Created with the built-in image-generation tool during design exploration on 17 October 2026. The user's reference images informed the cartoon style and seated composition. These PNGs are concept artwork, not editable SVG illustrations or animation rigs.

Original generation folder on this computer:

```text
/home/okello/.codex/generated_images/01a145f7-1109-72d3-8c01-16ae2c1b5736/
```

| Original generated filename | Repository copy |
| --- | --- |
| `exec-f08ea71f-dd35-4758-83d7-1332c6c82387.png` | `drivetest-results-blanket-v1.png` |
| `exec-40b61e15-54ea-452f-945a-bf6473d7a7b9.png` | `drivetest-welcome-concept-sheet-v1.png` |
| `exec-f25a6acd-ac32-4bf6-a352-ce79e32e7219.png` | `drivetest-seated-concept-sheet-v1.png` |
| `exec-c1859592-7574-45e3-98ab-0e4ee4d76d3f.png` | `drivetest-results-no-blanket-v1.png` |

Do not depend on the original generation folder for deployment. Preserve the repository masters and make versioned derivatives rather than overwriting them.

## 5. Where and how to use the mascot

| Screen / location | Pose | Behaviour and placement |
| --- | --- | --- |
| Welcome / quiz selection | Waving standing concept, if approved | A friendly introduction near “Start quiz.” Secondary to the category choices |
| During questions | Small gesturing concept, optional | Neutral encouragement. Must not point at a correct answer or suggest whether an unsubmitted answer is right |
| Results page | Blanket-and-drink armchair pose | On desktop, place to the left of the score so she looks toward it. On mobile, use a smaller image near the score without pushing actions far down the page |
| Share-score area | Right-hand hands-on-cheeks seated concept | Place beside or above a clearly labelled “Share my score” button, or inside a share card |
| Wrong-answer feedback | No dedicated asset approved yet | Use supportive wording. Do not mock, scold, or shame the player |
| Loading / error states | No dedicated asset approved yet | Keep actual status text visible; never imply a failed submission was saved |

### Sharing pose is not production-ready yet

The hands-on-cheeks pose currently exists only on the right half of a two-character concept sheet. Prepare a separate transparent asset before implementation; **do not display the whole sheet next to the share button**. Keep the excluded left-hand pose out of the public site.

A full-body illustration is too detailed to replace a small share icon. Use the mascot as supporting artwork and retain a normal, accessible text button. A separate close-up may be created later if a compact version is needed.

### Asset preparation before shipping

1. Keep the PNG masters unchanged.
2. Produce a standalone sharing pose and any approved welcome pose.
3. Check all cutout edges on white, cream, green, and dark backgrounds. All four files have RGBA channels, but alpha alone does not prove a clean cutout. The older two-pose sheets contain partially transparent pixels and need visual review before reuse.
4. Export suitably sized, compressed web derivatives while preserving transparency. Do not load full concept sheets for tiny illustrations.
5. Set image width and height to prevent layout movement. Preserve aspect ratio and avoid stretching.
6. Use an empty `alt` attribute when the mascot is decorative and the nearby text communicates the message. Give meaningful alternative text only when the artwork supplies information not otherwise present.
7. If animation is added later, respect reduced-motion preferences and avoid constant movement during questions. No animated mascot assets exist yet.
8. Keep image filenames neutral. Question images, alternative text, and SVG metadata should not inadvertently reveal an answer before submission.

Suggested derivative names, **not existing files**:

```text
drivetest-results-blanket-480.webp
drivetest-share-cheeks-v1.png
drivetest-share-cheeks-320.webp
drivetest-welcome-wave-v1.png
```

## 6. What the quiz needs

### Player experience

The initial site should support this flow:

1. Open the site without logging in.
2. Choose a topic, or choose mixed practice.
3. See the number of questions and how answering works.
4. Answer one question at a time using touch, mouse, or keyboard.
5. Receive feedback appropriate to the chosen quiz mode.
6. View a score, review answers, and try another quiz.
7. Share the result without being required to supply an email or create an account.

Suggested topic choices:

- Sign names and meanings.
- Classes.
- Subcategories.
- General road knowledge / driving responses.
- Mixed practice.

Do not show a topic as available if it has no reviewed, published questions. Handle short question pools honestly rather than repeating questions to reach an advertised length.

### Question formats

| Format | Example | Answer control |
| --- | --- | --- |
| Identify a sign | “What does this sign mean?” | One correct option, with a sign image |
| Identify a class | “Which class does this sign belong to?” | One correct option |
| Identify a subcategory | “Which subcategory contains this sign?” | One correct option |
| General knowledge | “What should a driver do when approaching this sign?” | One correct option, optional image |
| Multiple correct answers | “Which of these signs are regulatory?” | Checkboxes; explicitly say “Select all that apply” |
| Several questions about one sign | Ask its name, class, subcategory, and driving response | Separate question records linked to the same sign |

“Multiple questions” and “multiple correct answers” are separate capabilities. Support both. Avoid asking a sign's subcategory when it is unassigned or not applicable.

### Proposed marking rules

- Single-answer questions: one point for the correct choice, otherwise zero.
- Multiple-answer questions: recommended initial rule is one point only if the selected set exactly matches the correct set. State this before play; partial credit is a later product decision.
- Calculate scores on the server for real quizzes. The prototype's client-side scoring is only a demonstration.
- Do not accept a client-supplied total as the official result.
- Practice mode can explain each answer immediately. A future test mode can defer feedback until completion; decide this before building both modes.
- If a set asks several related questions about one sign, immediate feedback may reveal answers to later questions. Either defer group feedback or treat this explicitly as guided learning.
- Store the question version and option order used for an attempt so later edits do not change an existing score or review.

## 7. Question bank and owner-provided content

Questions should be separate from sign records. A sign can have many questions; a general question can exist without a sign image.

### Fields the question editor needs

| Field | Purpose |
| --- | --- |
| Stable question ID | Preserve references when wording changes |
| Question text | What the player is asked |
| Type | Single-answer or multiple-answer |
| Topic | Sign meaning, class, subcategory, general knowledge, etc. |
| Related sign ID | Optional link to existing sign artwork and metadata |
| Options with stable IDs | Display choices without relying on letters as permanent identifiers |
| Correct option IDs | Private marking key; never sent with an unanswered question |
| Explanation | Helpful learning feedback |
| Source / reviewer notes | Evidence and editorial context; private unless intentionally published |
| Draft / published status | Prevent unfinished questions entering quizzes |
| Version / update timestamp | Keep attempts and reviews consistent after edits |
| Group ID, optional | Connect a sequence of questions about the same sign |

The editor should allow adding, editing, previewing, saving drafts, and publishing. Validate that questions have enough distinct choices, a valid answer key, and a single correct choice when the type requires one. Publication should require a content review, not just valid form fields.

### How the owner can supply questions

Send questions in a readable format such as:

```text
Topic: Classes
Type: Single answer
Question: Which class contains warning signs?
A: Class A
B: Class B
C: Class C
Correct answer: B
Explanation: Warning signs belong to Class B in this catalog.
Related sign: None
```

For several correct answers:

```text
Topic: Regulatory subcategories
Type: Multiple answers
Question: Which of these are subcategories of Class A? Select all that apply.
A: Priority
B: Facility
C: Compulsory
D: Prohibitory
Correct answers: A, C, D
Explanation: Class A includes priority, prohibitory, and compulsory signs.
```

These examples follow the project's requested taxonomy. Driving advice and official sign meanings need their own source review before publication. Do not silently invent correct answers for ambiguous questions.

## 8. Sign classification and naming

| Class | Name | Subcategories |
| --- | --- | --- |
| A | Regulatory signs | Priority, prohibitory, compulsory |
| B | Warning signs | No subcategory required initially |
| C | Informatory signs | Advance directional, route confirmatory, facility |

- Priority includes Stop and Give way.
- Use the reviewed name from the catalog; do not reconstruct it from the SVG filename.
- Preserve stable IDs when names change.
- Warning names should use “ahead” where required, without duplicating the word.
- Use “compulsory” for the relevant regulatory category; do not classify every blue sign as compulsory.
- Correct spelling: **Miscellaneous**, not “miscellanous.”
- Miscellaneous is not automatically a new class or subcategory. Review its intended meaning and placement.
- Unclear classifications must be resolved before using them as quiz answer keys.

Existing source material includes [signs/manifest.json](signs/manifest.json), [sign-labels.json](sign-labels.json), [signs_metadata.json](signs_metadata.json), [signs_labels.csv](signs_labels.csv), and [signs/svg/](signs/svg/). See section 15 below for library coverage, editing, and regeneration.

The future connected editor should save authoritative changes to the database and reload them after refresh. Current browser-local edits are not automatic database updates; export/import remains necessary where the existing tools require it.

## 9. Public quiz and private administration

Keep these responsibilities separate:

| Public player area | Private owner/admin area |
| --- | --- |
| Published questions and sign content | Draft signs and draft questions |
| Start an anonymous attempt | Create and edit questions and answers |
| Submit answers | Edit names, classes, and subcategories |
| See own results and review | Manage images and publication |
| Open a shareable score page | Manage access and editorial notes |

The browser editor uses built-in session authentication; Sanctum remains an option for future mobile authentication. Admin access also needs authorization checks; being logged in alone must not grant editing permission.

### Security requirements carried forward from the review

- Add named rate limits for catalog reads, quiz creation, submissions, and admin login. Tune limits so image loads and people on shared networks are not unnecessarily blocked.
- Keep correct answers and explanations that reveal them out of unanswered-question responses.
- Use expiring anonymous attempt credentials and unpredictable public result identifiers. A result link must not grant permission to submit or modify an attempt.
- Finalise each attempt once; retries must not award points twice.
- Apply HTTPS at deployment, disable production debug output, configure secure cookies and trusted proxies correctly, and keep secrets out of the repository.
- Configure CORS for the actual frontend origins when cookie-based administration is introduced. CORS does not replace authentication, authorization, or CSRF protection.
- Keep draft-preview endpoints limited to local development. Staging previews need real authentication.
- Validate and safely render supplied question text and nicknames. Validate/sanitize future uploads, including SVGs.
- Do not place shared admin passwords or master API keys in the frontend or mobile app.
- Define retention for anonymous attempts and results before deployment. Collect only information needed for the quiz and sharing.

The catalog is intentionally public. A player can look up a sign's name, class, or subcategory. Present results as **practice scores**, not certified examinations or proof of driving competence. Authentication cannot prevent copying content that someone is allowed to see.

## 10. Score sharing requirements

The results page should show the score, total questions, percentage, topic, and clear next actions. “Review answers,” “Try again,” and “Share my score” are useful initial actions.

The future shared page should:

- Use a server-stored result and an unpredictable URL.
- Display only the score, quiz/topic description, and an optional nickname if the player chooses to include it.
- Avoid exposing attempt credentials, raw answers, private notes, email addresses, or other private data.
- Show a friendly preview image when shared, with the mascot and legible score where supported.
- Offer native sharing where available and a copy-link fallback.
- Confirm successful copying or sharing accurately; opening a share dialog does not prove a post was published.
- Handle expired, deleted, or unknown results with a helpful message.

Do not include a leaderboard in the initial scope unless requested. A public ranking would need additional decisions about abuse, duplicate attempts, names, and moderation.

## 11. Responsive design and accessibility requirements

- Support narrow mobile screens and desktop layouts without horizontal scrolling.
- Keep the sign large and crisp, with its full border visible.
- Put question wording and answer choices before decorative content in reading order.
- Use labelled native radio buttons for single answers and checkboxes for multiple answers.
- Provide generous touch targets, visible focus, and full keyboard operation.
- Do not rely on colour or animation to explain correctness.
- Announce submitted-answer feedback and results to assistive technology without repeatedly announcing every decorative update.
- Provide a meaningful text alternative for sign-identification questions that describes the visible symbol without simply giving away the answer. Decorative mascot images generally use empty alternative text.
- Keep buttons disabled only when necessary and explain what is required to proceed.
- Show network errors and allow safe retries. Do not discard selected answers silently.
- Treat refresh/resume behaviour as a deliberate feature: define attempt expiry and restore valid server-backed progress when supported.
- Keep untimed practice available. Offer the optional timed challenge described in section 17; never impose a timer on every player.

## 12. Implementation sequence and completion checks

### First: confirm content and prepare assets

- Review sign names, classes, subcategories, and meanings.
- Prepare a starter set of reviewed questions across the requested topics.
- Implement the starting quiz lengths and mode-specific feedback rules in section 17; tune durations after usability testing.
- Separate the sharing mascot from its concept sheet and optimise approved assets.
- Apply and test the colour tokens across questions, answers, results, and errors.

### Next: build the quiz and editor

- Implement question/options/version storage and anonymous attempt storage.
- Build protected question and sign editing with draft/publish controls.
- Implement public quiz creation, answer submission, server-side marking, and results.
- Connect the responsive frontend to the API.
- Implement score sharing and answer review.
- Add the security controls listed above before public deployment.

### Before launch

- Confirm guest players can finish and share without an account.
- Confirm multiple-answer marking follows the stated rule.
- Confirm question edits do not alter old results.
- Confirm repeated submissions cannot change a final score.
- Confirm draft content and answer keys do not leak through question responses.
- Confirm ordinary players cannot access admin actions.
- Confirm editor changes survive refresh and a new browser session.
- Test keyboard use, mobile layout, colour contrast, network failures, and missing-result states.
- Check production settings, backups, and a restore process.
- Verify the mascot does not conceal content and no rejected pose appears in public UI.

## 13. Decisions still open

1. Mascot name, if one is wanted.
2. Final approval of welcome and standalone sharing artwork.
3. Whether to expose the optional 20-question mode at first launch; the starting default is 10.
4. Final time allowances after trials; the starting challenge is 10 questions in 5 minutes.
5. Whether to introduce per-question speed challenges after whole-quiz timing works. Section 17 defines the proposed baseline for navigation and unanswered questions.
6. Retention period for anonymous attempts and shared results.
7. Whether optional nicknames are needed at launch.
8. Production domain, hosting, and admin account setup.

Keep this README current as those decisions are made. Update the status table when a planned feature becomes implemented and verified.

## 14. API setup, endpoints, and content operations

### Daily development

The installed backend uses Laravel 13, PHP 8.3, Composer, and MySQL 8. The existing project database is `drivetest`; the application account is `drivetest_app`. Read credentials from the private Laravel configuration, never from this document. Do not commit `.env` or use the MySQL root account in the application.

```bash
cd /home/okello/Documents/projects/DriveTest/api
php artisan serve --host=127.0.0.1 --port=8001
```

| Address | Purpose |
| --- | --- |
| `http://127.0.0.1:8001/quiz` | Public quiz frontend; currently requires published signs |
| `http://127.0.0.1:8001/quiz?demo=1` | Local-only sample quiz, independent of database content |
| `http://127.0.0.1:8001/api/v1/classes` | Taxonomy JSON |
| `http://127.0.0.1:8001/api/v1/preview/signs` | Local-only draft catalog preview |
| `http://127.0.0.1:8000/signs/index.html` | Separate static gallery, if its server is running |

To run the optional gallery server, use a separate terminal at the repository root:

```bash
cd /home/okello/Documents/projects/DriveTest
python3 -m http.server 8000 --bind 127.0.0.1
```

Leave these servers running while using their pages; stop them with Ctrl+C in their terminals. If a port is already in use, check the existing server before starting another. PHP API routes will not work on the Python gallery server.

### First setup on a new machine only

Install compatible PHP/extensions, Composer, and MySQL before using the existing application. Install locked PHP dependencies with `composer install` in `api/`. Create a private `.env` from `.env.example` only if none exists, and generate an application key with `php artisan key:generate` only during initial setup; do not replace an existing key or environment file during routine startup.

The local setup helper can create a **new** database and application account:

```bash
cd /home/okello/Documents/projects/DriveTest/api
sudo -v
php artisan app:setup-mysql
php artisan migrate
```

The helper refuses to overwrite an existing database/account and stores generated credentials in `.env`. Enter sudo credentials in your own terminal. This computer already has a configured project database; these commands are not a fix for an empty public quiz. Do not rerun initial setup or reset the database just to show questions.

### Implemented read endpoints

| Method | Path | Behaviour |
| --- | --- | --- |
| GET | `/api/v1/classes` | A/B/C taxonomy and subcategories; no database query required |
| GET | `/api/v1/signs` | Paginated published signs |
| GET | `/api/v1/signs/{id}` | Published sign detail, otherwise 404 |
| GET | `/api/v1/signs/{id}/image` | Published SVG from private storage, with SVG safety headers |
| GET | `/api/v1/preview/signs` | Draft/published catalog in local loopback development only |
| GET | `/api/v1/preview/signs/{id}` | Local preview detail including review notes |
| GET | `/api/v1/preview/signs/{id}/image` | Local preview image |

List filters: `class`, `subcategory`, `search`, `page`, and `per_page`. Default page size is 20, maximum 100. Invalid filters and mismatched class/subcategory selections return 422. IDs are stable strings; editing a name must not change an ID.

```bash
curl -H 'Accept: application/json' http://127.0.0.1:8001/api/v1/classes
curl -H 'Accept: application/json' 'http://127.0.0.1:8001/api/v1/signs?class=A&subcategory=priority&per_page=20'
```

The current resource includes `id`, `name`, `class`, `subcategory`, `meaning`, `image_url`, and `status`; `review_notes` is preview-only. Database columns use `class_code` and `subcategory_id`; older design sketches using `class_id` were proposals, not the implemented schema. MySQL is accessed by Laravel, not directly by browser/mobile clients.

PHP client example:

```php
<?php
$client = curl_init('http://127.0.0.1:8001/api/v1/classes');
curl_setopt_array($client, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER => ['Accept: application/json'],
    CURLOPT_TIMEOUT => 10,
]);
$response = curl_exec($client);
if ($response === false) {
    throw new RuntimeException(curl_error($client));
}
$status = curl_getinfo($client, CURLINFO_RESPONSE_CODE);
curl_close($client);
if ($status !== 200) {
    throw new RuntimeException('API returned HTTP '.$status);
}
print_r(json_decode($response, true, 512, JSON_THROW_ON_ERROR));
```

### Import and publication

Export the latest browser label changes before importing. Use a dry run first:

```bash
cd /home/okello/Documents/projects/DriveTest/api
php artisan signs:import ../sign-labels.json --dry-run
```

After reviewing the proposed import, run the same command without `--dry-run`. The importer matches stable IDs, preserves supplied names, retains existing meanings if absent, copies approved source artwork to private storage, and resets imported records to draft. Missing entries are not deleted. Unknown IDs, duplicate IDs, and artwork/path substitutions are rejected for separate review.

The publication command accepts exactly one selector: `--id` (repeatable), `--class`, or `--all`. Prefer explicit reviewed IDs. Example preview, not evidence this sign has been reviewed:

```bash
php artisan signs:publish --id=r01-stop --dry-run
```

Remove `--dry-run` only after review; the command asks for confirmation. `--unpublish` returns matching records to draft. Bulk publication does not perform review. Preserve the public draft filter and use the local demo for interface experiments.

### Checks

```bash
cd /home/okello/Documents/projects/DriveTest/api
php artisan route:list --except-vendor
php artisan test --compact
```

Database-backed tests must use a separate disposable test database, not `drivetest`. Existing tests do not prove all planned quiz features; section 1 records the review and acceptance criteria. Never expose `.env` or credentials in test output or documentation.

## 15. SVG library and label-editing workflow

The catalog contains vector redraws based on `IMG-20261014-WA0091.jpg` and `IMG-20261014-WA0092.jpg`. Coverage includes warning, regulatory, information/facility, direction, supplementary, street-name, and hazard-marker signs. Repeated signs are represented once; the standalone blue U-turn is included. The steering-wheel chart, cropped pedal instructions, dashboard symbols, road photograph, hand-signal sheet, and poster branding were excluded from this sign library.

Use the current manifest for counts, not old “147 signs” headings or old generated archives. The four supplementary panels were combined into one Additional panels entry, reducing the active catalog. Some old SVG files may remain on disk without belonging to the current manifest.

These are hand-constructed redraws, not certified official artwork. People, animals, vehicles, and service symbols may be simplified. Small lettering, distances, and meanings require review; illegible gradient numbers were omitted. White sign faces are retained, outer backgrounds are transparent, and text rendering depends on available fonts. SVG titles/descriptions and source notes help editorial review. Library IDs are not official regulatory codes.

### Labels and persistence

1. Open `signs/index.html` for the SVG gallery or `labeling_tool.html` for the other label tool. Root `index.html` currently redirects to the latter.
2. Change the label. Current tools save browser-local edits; storage differs between `file://`, `localhost`, and `127.0.0.1` origins.
3. Export JSON to preserve a portable copy. Do not assume an edit made in one origin appears in another browser or in MySQL.
4. Review and import the export using the CLI workflow above. Existing metadata, CSV, and generator overrides must remain aligned when synchronising files.
5. Verify the intended name in the relevant preview/API. Editing a label does not automatically alter lettering drawn inside the SVG itself.

Important files:

| Path | Purpose |
| --- | --- |
| `signs/manifest.json` | Active SVG catalog and source metadata |
| `sign-labels.json` | Exported labels used for import |
| `signs_metadata.json`, `signs_labels.csv` | Related label metadata/export representations |
| `signs/catalog-labels.json` | Stable-ID name overrides used by the generator |
| `signs/build_signs.py` | SVG and gallery generator |
| `signs/label_rules.py`, `signs/label-rules.js` | Naming and saved-label handling |
| `signs/backups/` | Prior artwork/label snapshots |
| `signs/road-signs-svg.zip` | Generated library package, not a second documentation authority |

Running `python3 signs/build_signs.py` overwrites generated SVGs, manifest, and gallery. Preserve custom edits in the generator and overrides, back up/export browser edits, and review output before regenerating. Do not use regeneration merely to fix a displayed label. The generator now includes this root README in the ZIP rather than writing another independent README under `signs/`.

## 16. Documentation ownership

- **This root README is the single project guide:** setup, current implementation, product requirements, colours, mascot, API use, content workflow, and correction plan.
- **`api/AGENTS.md` is for coding agents:** Laravel conventions and tooling rules. It points here for product decisions and must not duplicate the feature specification.
- **`api/CLAUDE.md` is only a compatibility pointer** to those same instructions, not a second copy of them.
- Dependency files in `vendor/` and `node_modules/` belong to their packages and should not be consolidated or edited.
- ZIP exports include a snapshot of this README. Update them from the root source; never edit the packaged copy as an independent guide.
- Update implementation status when work is completed. Keep dated review findings historical and record subsequent fixes explicitly, so a proposed feature is never mistaken for an existing one.

## 17. Quiz generation, length, and timing

### Goal and current status

The owner wants very many combinations drawn from signs, classes, subcategories, and questions supplied later, with optional timing. Generate each attempt on demand from reviewed content. Do not create or store a million full quizzes in advance, and do not invent a million near-duplicate questions.

The connected implementation now provides server selection, marking and whole-quiz timing. The requirements below also include future enhancements; the current implementation section above states what is available.

### How millions of combinations arise

For a pool of `n` eligible questions, selecting `k` distinct questions without caring about order gives `C(n,k) = n! / (k! × (n-k)!)` possible sets. A pool of **30 eligible questions gives 30,045,015 sets of 10**. Question ordering and answer shuffling can create additional presentations, but do not make the content itself new.

That figure assumes unrestricted selection from all 30. Topic quotas, sign exclusions, question groups, and difficulty rules reduce the number of eligible sets. Do not advertise the unrestricted figure as the actual variety of a constrained quiz. Random selection also does not guarantee global uniqueness; a repeated set across different users is acceptable. Do not keep a huge registry solely to prevent any two users ever receiving the same set.

For disjoint topic pools with exact quotas, the set count is the product of each pool's combination count. Questions eligible for multiple topics must be deduplicated and assigned deliberately; multiplying overlapping pools naively overcounts possibilities.

### Starting modes and lengths

These are product starting defaults from the discussion, adjustable after trials; they are not official driving-examination rules.

| Mode | Length | Timing | Feedback |
| --- | --- | --- | --- |
| Quick practice — default | 10 questions | Untimed | Check an answer, show its explanation, then continue |
| Timed challenge | 10 questions | 300 seconds for the whole attempt | Save selections while answering; show correctness and explanations after finalisation |
| Extended practice — optional | 20 questions | Untimed initially | Same learning feedback as quick practice |
| Per-question speed challenge — later | Configurable | Illustrative starting values: 20 seconds for identification, 40 seconds for longer multiple-answer questions | Define separate rules and test reading burden before enabling |
| Local UI demo — existing | 4 sample questions | Untimed | Client-side demonstration only; no saved/shareable result |

Ten questions is the recommended default, not an evidence-based universal optimum. Reassess completion rates, reading time, and learner feedback. A future timed 20-question mode needs its own disclosed duration; do not silently apply the 5-minute limit intended for ten questions.

Before starting, show topic/filter, actual number of questions, mode, duration if any, feedback policy, and marking rule. Start the timed attempt only when the player activates “Start challenge,” not while browsing topics.

### Separate content filters from interaction formats

- **Topic:** identification/meaning, class, subcategory, or general road knowledge.
- **Sign class filter:** A, B, C, or all eligible classes.
- **Subcategory filter:** applicable reviewed subcategory within its class; do not invent one for Class B.
- **Answer type:** single-answer radio controls or multiple-answer checkboxes. This is independent of topic.
- **Mode:** untimed practice, timed challenge, or a later speed mode.
- **Length:** default 10; optional 20 when sufficient content exists.

For example, “Warning signs only” is a content filter; it can be practised untimed or as a timed challenge. It should not require a separate duplicated question bank. Pure Class B selection makes “Which class?” trivial, so suppress or warn about that combination rather than padding the quiz with questions whose answer is exposed by the chosen filter.

### Mixed-quiz blueprint

| Topic | Slots in a 10-question mixed quiz |
| --- | ---: |
| Sign identification / meaning | 4 |
| Class identification | 2 |
| Subcategory identification | 2 |
| Owner-supplied general road questions | 2 |

Multiple-answer questions may occupy appropriate slots within these topics. Do not mechanically generate two correct options every time; the reviewed answer key decides the correct set. Aim for sensible coverage of A/B/C across eligible sign questions without forcing three classes into every small topic block.

If general questions are not yet available, the proposed interim blueprint is **6 identification/meaning + 2 class + 2 subcategory**. Tell the player the available mix before starting. If that pool is also insufficient, explicitly offer a shorter quiz or another filter. Never repeat questions, silently change topics, or unlock drafts merely to reach ten.

For optional 20-question mixed practice, start with doubled quotas only when sufficient eligible material exists. Treat focused modes as their own validated blueprints rather than applying mixed-mode quotas blindly.

### Server-side selection procedure

1. Validate the requested mode, length, filters, and blueprint against server configuration. The client cannot set arbitrary time allowances or scoring rules.
2. Load only published, reviewed question versions whose linked sign/media is approved for public use. Check classification applicability and required assets.
3. Build deterministic eligible pools; availability counts must not depend on a random dry-run selection.
4. Select without replacement by stable question ID. Avoid repeated signs in independent questions, including signs used in image answer choices where those would disclose later answers.
5. Treat intentional multi-question sign groups explicitly. Preserve group order and reserve enough slots for the whole group; do not split a group unexpectedly.
6. Where feasible, reduce repeats from this guest's recent attempts. A short pool may require repeats between attempts; relax recent-history preferences before breaking within-attempt uniqueness. Do not promise cross-device history without an account or transferable identity.
7. Shuffle questions within blueprint/group constraints and shuffle options only when permitted. Options like “all of the above” or ordered sequences should not be blindly shuffled; prefer order-independent authored choices.
8. Save the selected question versions, order, option order, scoring policy, and timer settings transactionally before serving the attempt. A stored seed alone is not sufficient if underlying questions can change.
9. Return only safe player-facing fields, not correct-option flags or answer-revealing explanations before the mode allows them.

A generated distractor is an editorial suggestion, not a reviewed answer option. Owner-authored questions must work even when there is no related sign image or catalog meaning field.

### Timing authority and refresh behaviour

Use server timestamps as the authority. Store `started_at`, `expires_at` (null for untimed), and a snapshotted time limit with the attempt. Return `server_now` and the deadline so the frontend can display remaining time without trusting the device clock.

- Display minutes and seconds as text, with an accessible timer label. Announce meaningful thresholds sparingly, not every second.
- Compute the countdown from the fixed deadline, not from a decrementing counter that pauses in background tabs.
- Refresh, reopening the tab, changing the device clock, or losing focus must not extend the deadline.
- Save selections as the player progresses; show saving/saved/failed state and a retry path. Selections not acknowledged by the server are not guaranteed saved.
- When time expires, finalise using the last accepted answers. Unanswered questions score zero. Reject new answer changes after the deadline even if a client timer says time remains.
- A server job may finalise idle expired attempts; all read/write/finalisation paths must also enforce expiry so correctness does not depend on job punctuality.
- Use a transaction/lock or equivalent atomic state transition to resolve concurrent submissions and expiry. Duplicate requests and retries must not create two results or change a completed score.
- Use server receipt time as the proposed baseline for deadlines; do not trust a browser's claimed send time. Any future network-grace policy must be explicit, bounded, and stored with the attempt.
- Untimed attempts can have a separate retention/abandonment expiry; label it as session expiry, not a hidden challenge timer.

Store timestamps consistently in UTC; localise any displayed dates for the user. A duration such as five minutes is independent of timezone.

### Answer navigation and finalisation

For quick practice, checking an answer locks it and reveals feedback; revisiting it should not award another point. For timed challenge, permit reviewing/changing saved selections before completion or deadline and mark only at the end. Show unanswered questions before voluntary early completion and let the player return to them. Unanswered items receive zero if the player confirms completion.

Single-answer scoring is one point for the correct option. Multiple-answer scoring is one point only for the exact correct set, with no extra choices. No negative marking or partial credit initially. Show this rule before starting and near multiple-answer controls. A future change to scoring must be versioned so historical scores remain reproducible.

Grouped practice questions need a deliberate feedback policy: defer the group's explanations until its final answer if early feedback would give away later answers. Do not infer “group” from coincidentally sharing a sign ID.

Results should identify mode, topic, score/total, percentage, and timeout versus voluntary completion. For timed results, show duration used when helpful. Share only server-stored summaries, without exposing attempt access credentials, private history, or answer keys.

## 18. Implementation map and theme contract

### Correct application folder

**Implement the quiz product in `/home/okello/Documents/projects/DriveTest/api/`.** This is the existing Laravel application serving `/quiz` and the API. Keep PHP/Laravel + MySQL and reuse the existing Vue frontend unless a deliberate architecture change is agreed.

Do not build a second quiz in root `index.html`, `labeling_tool.html`, or `signs/index.html`: those are catalog/labeling tools. The conversation's inline visualization is a prototype, not the application source. Do not change `api/public/vendor/vue.global.prod.js`; it is vendored third-party code.

| Area | Existing folder/file to use | Implementation responsibility |
| --- | --- | --- |
| Player UI and interactions | [api/public/assets/quiz/app.js](api/public/assets/quiz/app.js) | Mode/topic selection, question display, timer display, save/retry states, review, results and sharing; consume server decisions |
| Styling | [api/public/assets/quiz/quiz.css](api/public/assets/quiz/quiz.css) | Shared colour tokens, layout, responsive controls, feedback and timer states |
| HTML shell | [api/resources/views/quiz.blade.php](api/resources/views/quiz.blade.php) | Load the UI and safe initial configuration; keep local-demo gate |
| UI fixture | [api/resources/quiz-demo.json](api/resources/quiz-demo.json) | Four local sample questions only; never treat as the production question bank |
| Web routes | [api/routes/web.php](api/routes/web.php) | Player page; loads `quiz.php` for the editor and session APIs |
| API routes | [api/routes/api.php](api/routes/api.php) | Public catalog routes; session quiz/admin routes are in `routes/quiz.php` |
| Controllers | [api/app/Http/Controllers/Api/](api/app/Http/Controllers/Api/) | Request orchestration; delegate selection/marking to services |
| Validation | [api/app/Http/Requests/](api/app/Http/Requests/) | Mode/filter/length constraints, answer IDs and editor validation |
| Safe responses | [api/app/Http/Resources/](api/app/Http/Resources/) | Separate public question/result output from private editor and marking data |
| Business logic | [api/app/Services/](api/app/Services/) | Add selection, scoring and attempt lifecycle services; existing sign import remains separate |
| Data models | [api/app/Models/](api/app/Models/) | Add question/version/option/attempt/answer/result relationships as needed |
| Database changes | [api/database/migrations/](api/database/migrations/) | MySQL constraints, indexes and immutable attempt/version references |
| Test data | [api/database/factories/](api/database/factories/), [api/database/seeders/](api/database/seeders/) | Isolated fixtures and explicitly reviewed starter content; no automatic mass publication |
| Configuration | [api/config/](api/config/) | Existing `quiz.php` defines modes, lengths, quotas and deadlines |
| Middleware/security | [api/bootstrap/app.php](api/bootstrap/app.php), [api/app/Http/Middleware/](api/app/Http/Middleware/) | Rate limits, admin/session access, guest attempt protection |
| Automated checks | [api/tests/Feature/](api/tests/Feature/), [api/tests/Unit/](api/tests/Unit/) | API/DB lifecycle tests and isolated selection/scoring tests; add browser coverage using an agreed test setup |
| Canonical sign artwork | [signs/svg/](signs/svg/) | Reviewed source assets; serve via the existing controlled image delivery |
| Mascot masters | [assets/mascot/](assets/mascot/) | Preserve approved source illustrations and versioned derivatives |
| Runtime mascot images | [api/public/assets/mascot/](api/public/assets/mascot/) | Optimised frontend copies; blanket image exists, sharing derivative still needed |

The scaffold also contains `api/resources/js/app.js` and `api/resources/css/app.css`, but the current quiz Blade page does **not** load those Vite entrypoints. Editing them alone will not update the quiz. If switching to a bundled pipeline later, migrate the page references explicitly and eliminate competing active sources.

### Proposed persistence responsibilities

Current storage uses `questions` with options/keys in JSON and `quiz_attempts` with frozen items and answers in JSON. Versions increment on question edits; attempts preserve their own snapshots. The responsibilities below describe the model, not separate tables for each bullet.

- **Question and version:** stable identity, published immutable version, topic/class/subcategory applicability, optional sign/group, wording, explanation, source and review state.
- **Options:** stable per-version IDs, labels/images, private correctness flags and shuffle policy.
- **Attempt:** opaque ID, protected guest ownership, mode, filters, selected blueprint, expected count, status, start/deadline/completion timestamps, scoring policy version.
- **Attempt items:** frozen question version and option order, sequence/group membership; ensure no duplicate question where prohibited.
- **Answers:** selected option IDs, accepted/saved timestamp, locked state where applicable; update atomically within the active attempt's policy.
- **Result:** one final score per attempt, public opaque identifier, total, mode and approved share fields. Keep public result lookup separate from private review access.

Avoid putting the correct answers into generic catalog responses or exposing the private attempt credential in a shared URL. Do not let editing an option rewrite the interpretation of a past response.

### Visual theme to implement

Use the existing **warm road-learning light theme**, not a new dashboard skin. Section 2 remains the full colour specification:

| Role | Value / rule |
| --- | --- |
| Main background | Warm cream `#F7F4EC` |
| Cards and sign faces | White `#FFFFFF` |
| Reading text | Asphalt charcoal `#252A28` |
| Main actions / selected state | Forest green `#215B46` with white button text |
| Small highlights / approaching deadline | Road amber `#E7AD35` with charcoal text; never white-on-amber labels |
| Restrained brand accent | Burgundy `#8B263B`, primarily carried by mascot hair |
| Current supporting colours | Green hover `#184435`, soft green `#E8F0EC`, error red `#B3261E`, soft error `#FBECEB`, muted text `#5F6663`; check contrast in each actual state |
| Typography | Current readable system sans-serif; avoid a new decorative font dependency |
| Layout | Clear question first, optional sign on white, readable choices, one primary next action; text-only questions use the full content width |

Keep colours in the `--dt-*` tokens in `quiz.css`; do not create a separate palette in each component. Keep the interface free of unrelated purple/neon styling or decorative gradients. Dark mode is not part of the initial theme and needs separately approved/tested tokens. Preserve the actual sign colours, even when they differ from the UI palette.

For timed modes, a compact text timer and a subtle indicator are enough. Use a labelled amber warning near expiry; use a readable “Time is up” state at the deadline. Avoid flashing red, constant animation, or announcing every second to a screen reader. Timing must not cover the question or reduce option touch targets.

Use the blanket-and-drink mascot to the left of results on desktop, smaller above/near results on mobile. Use only the right-hand hands-on-cheeks concept for a future standalone sharing asset. Never ship the rejected rear-facing pose or an entire multi-pose sheet. Do not introduce mascot animation as part of implementing timers.

### Delivery order and verification

1. Implement reviewed question/version storage and owner authoring/import; preserve existing sign IDs and edited labels.
2. Implement eligibility, blueprints, no-repeat selection and short-pool handling on the server.
3. Implement anonymous persisted attempts and marking, then connect the existing frontend for untimed practice.
4. Add whole-quiz timing with server-enforced expiry and mode-specific feedback/navigation.
5. Add saved result sharing and finish approved mascot integration; consider extended/per-question modes afterward.

Required checks in addition to section 1's acceptance list:

- Selection respects quotas, filters, published state, groups and option uniqueness; inadequate pools produce an explicit shorter offer or unavailable state.
- Clock-controlled tests cover just before, exactly at, and after the deadline. Define `server_now >= expires_at` as expired.
- Refresh/device-clock changes do not reset time; concurrent tabs/submissions cannot extend time or finalise twice.
- Duplicate answer requests, network retries and late packets cannot overwrite a final score.
- Exact-set scoring handles missed correct options and additional wrong options; historical question edits do not affect saved attempts.
- Timed challenge feedback stays private until completion; practice feedback appears only after the relevant answer/group locks.
- Guest attempts and private review cannot be retrieved using another guest's credential or a public result ID.
- The same public API behaviour can later serve mobile clients; timer authority is never frontend-specific.
- Browser checks cover mobile/desktop, keyboard interaction, long questions, image and text-only choices, timer thresholds, retry/error states, expiry and shared results.

## 19. Importing typed and handwritten questions

The owner may supply questions and answers as pasted text, photos, scans, screenshots, or documents. Assistance should distinguish printed/typed content from handwriting, ticks, circles, crossed-out text, and margin notes instead of merging them into one assumed authoritative answer.

### Extraction workflow

1. Preserve the original attachment/source and identify the page and question number.
2. Transcribe the printed question and printed options separately from handwritten additions. Preserve wording before proposing spelling or punctuation cleanup.
3. Describe marks literally: for example, “handwritten tick beside B,” “C circled,” or “B crossed out, D written above.” A mark can indicate a student's answer, a correction, or a teacher's note; it does not by itself prove correctness.
4. Identify uncertain characters/words and whether the writing is printed or handwritten with appropriate confidence. Use `[unclear]` or list possible readings; never silently guess an answer key.
5. Present a proposed structured question, its candidate answer, and explanation separately from the verbatim extraction. Flag conflicting printed and handwritten keys for owner confirmation.
6. After clarification, import as a draft, preview it, and review before publishing. Preserve the source and rationale for the chosen key.

Suggested review table:

| Source / question | Printed text | Handwritten details | Candidate answer | Uncertainty / action |
| --- | --- | --- | --- | --- |
| Page 1, Q3 | Question and options as printed | Tick beside B; note in margin | B appears selected; correctness unverified | Confirm whether the tick is an answer or marking |

Supported interpretations include typed-only questions, handwritten-only questions, a printed worksheet with handwritten responses, and corrections over printed text. Poor resolution, overlapping strokes, stylised fonts, or faint pencil may prevent reliable separation. Request a clearer crop or owner transcription for the specific unclear region rather than claiming certainty.

### Information to retain for editorial review

- Source attachment/page/question reference and any related sign.
- Verbatim printed text and verbatim handwritten text in separate fields/notes.
- Mark locations and crossed-out alternatives, without silently discarding them.
- Proposed normalised wording and option IDs.
- Observed selected answer versus independently reviewed correct answer.
- Confidence/uncertainty notes, resolution, reviewer and draft/publication status.

Private scans may contain names, marks, or other personal information unrelated to the quiz. Keep source material in private editorial storage; publish only the reviewed question content. Do not place uploaded worksheets in `api/public/` as part of intake. Use the future protected editor/import workflow in `api/`, with drafts in MySQL and private uploads, rather than a second JSON-based production question bank.

A future OCR/extraction service can suggest text, but it is not a prerequisite for manual question entry and must not auto-publish inferred correct answers. For now, the owner can send an image here for transcription and review, then approve the structured draft for implementation.
