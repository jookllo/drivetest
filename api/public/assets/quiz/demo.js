/*
  DriveTest public quiz — Vue 3 (global build, no bundler).
  Reads signs from the Laravel API (/api/v1). Practice scoring is client-side
  and is a demonstration only (README section 6).
*/
(function () {
  "use strict";

  var API = "/api/v1";
  var QUIZ_LENGTH = 10;
  var CLASS_IDS = ["A", "B", "C"];
  var MASCOT = "/assets/mascot/drivetest-results-blanket-v1.png";
  var demoElement = document.getElementById("quiz-demo-data");
  var demoQuestions = demoElement ? JSON.parse(demoElement.textContent) : null;

  function shuffle(list) {
    var a = list.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i];
      a[i] = a[j];
      a[j] = t;
    }
    return a;
  }

  function sample(list, n) {
    return shuffle(list).slice(0, n);
  }

  function uniqueBy(list, keyFn) {
    var seen = Object.create(null);
    return list.filter(function (item) {
      var k = keyFn(item);
      if (seen[k]) {
        return false;
      }
      seen[k] = true;
      return true;
    });
  }

  function sameSet(a, b) {
    if (a.length !== b.length) {
      return false;
    }
    var s = a.slice().sort();
    var t = b.slice().sort();
    return s.every(function (v, i) {
      return v === t[i];
    });
  }

  function practiceLabel(label) {
    return /practice$/i.test(label) ? label : label + " practice";
  }

  function optionSet(correctLabel, distractorLabels) {
    var opts = [{ label: correctLabel, correct: true }];
    distractorLabels.forEach(function (label) {
      opts.push({ label: label, correct: false });
    });
    opts = shuffle(opts);
    opts.forEach(function (o, i) {
      o.id = "opt" + i;
    });
    return {
      options: opts.map(function (o) {
        return { id: o.id, label: o.label, image: null };
      }),
      correctIds: opts
        .filter(function (o) {
          return o.correct;
        })
        .map(function (o) {
          return o.id;
        }),
    };
  }

  function explanationFor(sign) {
    if (sign.meaning) {
      return sign.meaning;
    }
    var bits = ['This sign is "' + sign.name + '".'];
    if (sign.classLabel) {
      bits.push("Class: " + sign.classLabel + ".");
    }
    if (sign.subcategoryLabel) {
      bits.push("Subcategory: " + sign.subcategoryLabel + ".");
    }
    return bits.join(" ");
  }

  function otherNames(catalog, sign, count) {
    var same = catalog.filter(function (s) {
      return s.id !== sign.id && s.classCode === sign.classCode && s.name !== sign.name;
    });
    var other = catalog.filter(function (s) {
      return s.id !== sign.id && s.name !== sign.name;
    });
    return uniqueBy(sample(same, count).concat(sample(other, count)), function (s) {
      return s.name;
    }).map(function (s) {
      return s.name;
    });
  }

  function otherMeanings(catalog, sign, count) {
    var pool = catalog.filter(function (s) {
      return s.meaning && s.meaning !== sign.meaning;
    });
    return uniqueBy(sample(pool, count), function (s) {
      return s.meaning;
    }).map(function (s) {
      return s.meaning;
    });
  }

  function qName(catalog, sign) {
    var names = otherNames(catalog, sign, 3);
    if (names.length < 3) {
      return null;
    }
    var set = optionSet(sign.name, names);
    return {
      type: "single",
      topicId: "names",
      prompt: "What is this sign?",
      sign: sign,
      options: set.options,
      correctIds: set.correctIds,
      explanation: explanationFor(sign),
    };
  }

  function qMeaning(catalog, sign) {
    if (!sign.meaning) {
      return null;
    }
    var distractors = otherMeanings(catalog, sign, 3);
    if (distractors.length < 2) {
      return null;
    }
    var set = optionSet(sign.meaning, distractors);
    return {
      type: "single",
      topicId: "meanings",
      prompt: "What does this sign mean?",
      sign: sign,
      options: set.options,
      correctIds: set.correctIds,
      explanation: explanationFor(sign),
    };
  }

  function qClass(catalog, sign) {
    if (!sign.classLabel) {
      return null;
    }
    var labels = uniqueBy(
      catalog.filter(function (s) {
        return s.classLabel;
      }),
      function (s) {
        return s.classLabel;
      }
    ).map(function (s) {
      return s.classLabel;
    });
    var distractors = labels.filter(function (l) {
      return l !== sign.classLabel;
    });
    if (distractors.length < 1) {
      return null;
    }
    var set = optionSet(sign.classLabel, sample(distractors, 2));
    return {
      type: "single",
      topicId: "classes",
      prompt: "Which class does this sign belong to?",
      sign: sign,
      options: set.options,
      correctIds: set.correctIds,
      explanation: explanationFor(sign),
    };
  }

  function qSubcategory(catalog, sign) {
    if (!sign.subcategoryLabel) {
      return null;
    }
    var siblings = uniqueBy(
      catalog.filter(function (s) {
        return s.classCode === sign.classCode && s.subcategoryLabel;
      }),
      function (s) {
        return s.subcategoryLabel;
      }
    ).map(function (s) {
      return s.subcategoryLabel;
    });
    if (siblings.length < 2) {
      return null;
    }
    var distractors = siblings.filter(function (l) {
      return l !== sign.subcategoryLabel;
    });
    var set = optionSet(sign.subcategoryLabel, sample(distractors, 2));
    return {
      type: "single",
      topicId: "subcategories",
      prompt: "Which subcategory does this sign belong to?",
      sign: sign,
      options: set.options,
      correctIds: set.correctIds,
      explanation: explanationFor(sign),
    };
  }

  function qClassMulti(catalog, targetClassCode) {
    var inClass = catalog.filter(function (s) {
      return s.classCode === targetClassCode;
    });
    var outClass = catalog.filter(function (s) {
      return s.classCode && s.classCode !== targetClassCode;
    });
    if (inClass.length < 1 || outClass.length < 1) {
      return null;
    }
    var correctSigns = sample(inClass, 2);
    var wrongSigns = sample(outClass, 2);
    var signs = shuffle(correctSigns.concat(wrongSigns));
    var classLabel = correctSigns[0].classLabel;
    var shortClass = classLabel.replace(/\s*signs?$/i, "").toLowerCase();
    var correctIds = [];
    var options = signs.map(function (s, i) {
      var id = "opt" + i;
      if (s.classCode === targetClassCode) {
        correctIds.push(id);
      }
      return { id: id, label: s.name, image: s.image };
    });
    return {
      type: "multi",
      topicId: "classes",
      prompt: "Which of these signs are " + shortClass + " signs?",
      signs: signs,
      options: options,
      correctIds: correctIds,
      explanation:
        classLabel +
        ": " +
        correctSigns
          .map(function (s) {
            return s.name;
          })
          .join(", ") +
        ".",
    };
  }

  function eligibleSigns(catalog, topicId) {
    return catalog.filter(function (sign) {
      if (topicId === "names") {
        return qName(catalog, sign) !== null;
      }
      if (topicId === "meanings") {
        return qMeaning(catalog, sign) !== null;
      }
      if (topicId === "classes") {
        return qClass(catalog, sign) !== null;
      }
      if (topicId === "subcategories") {
        return qSubcategory(catalog, sign) !== null;
      }
      return true;
    });
  }

  function makeSingle(catalog, topicId, sign) {
    if (topicId === "names") {
      return qName(catalog, sign);
    }
    if (topicId === "meanings") {
      return qMeaning(catalog, sign);
    }
    if (topicId === "classes") {
      return qClass(catalog, sign);
    }
    if (topicId === "subcategories") {
      return qSubcategory(catalog, sign);
    }
    return null;
  }

  function buildQuiz(catalog, topicId) {
    if (topicId === "mixed") {
      var pool = shuffle(catalog);
      var questions = [];
      var used = Object.create(null);
      var multiBudget = 2;
      var types = ["names", "meanings", "classes", "subcategories"];
      for (var i = 0; i < pool.length && questions.length < QUIZ_LENGTH; i++) {
        var sign = pool[i];
        if (used[sign.id]) {
          continue;
        }
        var q = null;
        if (multiBudget > 0 && questions.length >= 2) {
          q = qClassMulti(catalog, CLASS_IDS[Math.floor(Math.random() * CLASS_IDS.length)]);
          if (q) {
            multiBudget--;
            q.signs.forEach(function (s) {
              used[s.id] = true;
            });
            questions.push(q);
            continue;
          }
        }
        var type = types[Math.floor(Math.random() * types.length)];
        q = makeSingle(catalog, type, sign) || makeSingle(catalog, "names", sign);
        if (q) {
          used[sign.id] = true;
          questions.push(q);
        }
      }
      return questions;
    }
    return shuffle(eligibleSigns(catalog, topicId))
      .slice(0, QUIZ_LENGTH)
      .map(function (sign) {
        return makeSingle(catalog, topicId, sign);
      })
      .filter(Boolean);
  }

  var TOPICS = [
    { id: "names", name: "Sign names", desc: "See a sign and choose its name." },
    { id: "meanings", name: "Sign meanings", desc: "Say what the sign tells a driver." },
    { id: "classes", name: "Classes", desc: "Regulatory, warning, or informatory — and select-all questions." },
    { id: "subcategories", name: "Subcategories", desc: "Priority, prohibitory, compulsory, and more." },
    { id: "mixed", name: "Mixed practice", desc: "A mix of every question type." },
  ];

  var TEMPLATE = [
    '<a class="skip-link" href="#main">Skip to main content</a>',
    '<header class="site-header"><div class="site-header__inner">',
    '  <a class="brand" href="#" @click.prevent="goHome"><span class="brand__mark"></span><span>DriveTest</span></a>',
    '  <span class="brand__sub">Road sign practice</span>',
    '  <span class="header-spacer"></span>',
    '  <button v-if="view===\'quiz\' || view===\'results\'" class="btn btn--ghost header-action" type="button" @click="goHome">Start over</button>',
    '</div></header>',
    '<main id="main" class="wrap">',
    '  <p v-if="isDemo" class="note"><strong>Local demo · 4 sample questions.</strong> Scores are illustrative, not saved or shareable. No signs have been published.</p>',

    /* HOME */
    '  <section v-if="view===\'home\'" class="view">',
    '    <p class="eyebrow">Practice, no account needed</p>',
    '    <h1>Learn the road signs</h1>',
    '    <p class="lede">Pick a topic and answer one question at a time. You get a score to practise with, an explanation for each answer, and a link you can share.</p>',
    '    <h2 class="section-title">Choose a topic</h2>',
    '    <div class="topic-grid">',
    '      <button v-for="t in topics" :key="t.id" class="topic" type="button" :disabled="t.count===0" @click="startQuiz(t.id)">',
    '        <span class="topic__name">{{ t.name }}</span>',
    '        <span class="topic__desc">{{ t.desc }}</span>',
    '        <span class="topic__count">{{ t.count===0 ? \'No questions available yet\' : t.count + \' questions\' }}</span>',
    '      </button>',
    '    </div>',
    '    <h2 class="section-title">How it works</h2>',
    '    <ol class="steps">',
    '      <li>Each quiz asks up to {{ quizLength }} questions from the topic you choose.</li>',
    '      <li>Questions with one answer use round buttons; questions with several answers use checkboxes and say “Select all that apply.”</li>',
    '      <li>Practice mode marks each answer as you go and explains it.</li>',
    '      <li>At the end you can review every answer, try again, or share your score.</li>',
    '    </ol>',
    '    <div class="note" role="note"><strong>Practice content.</strong> Questions come from the published sign catalog, which is still under review. Treat the score as practice, not a certified driving test. Topics with no reviewed questions are shown as unavailable.</div>',
    '  </section>',

    /* QUIZ */
    '  <section v-if="view===\'quiz\'" class="view">',
    '    <h1 class="visually-hidden">Quiz</h1>',
    '    <div class="quiz-top">',
    '      <span class="quiz-top__topic">{{ quiz.topicLabel }}</span>',
    '      <span class="quiz-top__count">Question {{ quiz.index + 1 }} of {{ quiz.questions.length }}</span>',
    '    </div>',
    '    <div class="progress" role="progressbar" aria-label="Quiz progress" aria-valuemin="0" aria-valuemax="100" :aria-valuenow="progressPct"><div class="progress__fill" :style="{ width: progressPct + \'%\' }"></div></div>',
    '    <div class="card" v-if="current">',
    '      <div class="question-layout" :class="{ \'question-layout--text\': !current.sign || !current.sign.image }">',
    '        <div class="sign-panel" v-if="current.sign && current.sign.image"><img :src="current.sign.image" alt="Road sign to identify"></div>',
    '        <div>',
    '          <p class="question-prompt" tabindex="-1" ref="promptEl">{{ current.prompt }}</p>',
    '          <span class="instruction" v-if="current.type===\'multi\'">Select all that apply. Choose every correct answer and no others for one point.</span>',
    '          <fieldset class="options" ref="optionsEl"><legend class="visually-hidden">Answer choices</legend>',
    '            <label v-for="opt in current.options" :key="opt.id" class="option" :class="optionClass(opt)">',
    '              <input :type="current.type===\'multi\' ? \'checkbox\' : \'radio\'" name="answer" :value="opt.id" :checked="isChosen(opt.id)" :disabled="isChecked" @change="choose(opt.id, current.type===\'multi\')">',
    '              <span class="option__label"><img v-if="opt.image" class="option__thumb" :src="opt.image" alt="">{{ opt.label }}</span>',
    '              <span v-if="markFor(opt.id)" class="option__mark" :class="markFor(opt.id)===\'Correct answer\' ? \'option__mark--correct\' : \'option__mark--wrong\'">{{ markFor(opt.id) }}</span>',
    '            </label>',
    '          </fieldset>',
    '          <div class="btn-row">',
    '            <button v-if="!isChecked" class="btn btn--primary" type="button" :disabled="!canCheck" @click="checkAnswer">Check answer</button>',
    '            <button v-else class="btn btn--primary" type="button" @click="nextQuestion">{{ isLast ? \'See results\' : \'Next question\' }}</button>',
    '          </div>',
    '          <div v-if="isChecked" class="feedback" :class="lastWasCorrect ? \'feedback--correct\' : \'feedback--wrong\'" role="status" aria-live="polite">',
    '            <p class="feedback__title">{{ lastWasCorrect ? \'Correct\' : \'Not quite\' }}</p>',
    '            <p class="feedback__text">{{ current.explanation }}</p>',
    '          </div>',
    '        </div>',
    '      </div>',
    '    </div>',
    '  </section>',

    /* RESULTS */
    '  <section v-if="view===\'results\' && result" class="view">',
    '    <h1>Your practice result</h1>',
    '    <div class="card"><div class="result-hero">',
    '      <div class="result-mascot"><img :src="mascot" alt="" width="1306" height="1205"></div>',
    '      <div>',
    '        <div class="score-line"><span class="score-big">{{ result.score }}</span><span class="score-of">/ {{ result.total }} correct</span><span class="score-pct">{{ result.pct }}%</span></div>',
    '        <p class="result-topic">{{ practiceLabel(result.topicLabel) }}</p>',
    '        <div class="btn-row">',
    '          <button class="btn btn--primary" type="button" :aria-expanded="reviewOpen ? \'true\' : \'false\'" @click="toggleReview">{{ reviewOpen ? \'Hide answers\' : \'Review answers\' }}</button>',
    '          <button class="btn btn--secondary" type="button" @click="startQuiz(result.topicId)">Try again</button>',
    '          <button v-if="!isDemo" class="btn btn--secondary" type="button" @click="shareResult">Share my score</button>',
    '        </div>',
    '        <p class="result-topic" role="status" aria-live="polite">{{ shareStatus }}</p>',
    '      </div>',
    '    </div></div>',
    '    <div class="review-list" v-if="reviewOpen">',
    '      <div v-for="(item, i) in reviewItems" :key="i" class="review-item" :class="item.correct ? \'review-item--correct\' : \'review-item--wrong\'">',
    '        <p class="review-item__prompt">{{ i + 1 }}. {{ item.prompt }}</p>',
    '        <p class="review-item__row"><span class="review-item__label">Your answer:</span> {{ item.your || \'No answer\' }}</p>',
    '        <p class="review-item__row"><span class="review-item__label">Correct: </span>{{ item.correctLabels }}</p>',
    '        <p class="review-item__explain">{{ item.explanation }}</p>',
    '      </div>',
    '    </div>',
    '  </section>',

    /* SHARED */
    '  <section v-if="view===\'shared\' && shared" class="view">',
    '    <div class="shared-card card">',
    '      <p class="eyebrow">Shared practice result</p>',
    '      <h1>DriveTest score</h1>',
    '      <p class="nickname" v-if="shared.name">{{ shared.name }}</p>',
    '      <div class="result-hero"><div>',
    '        <div class="score-line"><span class="score-big">{{ shared.s }}</span><span class="score-of">/ {{ shared.n }}</span><span class="score-pct">{{ sharedPct }}%</span></div>',
    '        <p class="result-topic">{{ practiceLabel(shared.ti || shared.t) }}</p>',
    '      </div></div>',
    '      <div class="btn-row" style="justify-content:center"><button class="btn btn--primary" type="button" @click="goHome">Take a quiz</button></div>',
    '      <p class="result-topic" style="margin-top:1rem">A self-reported practice score. DriveTest scores are practice only and are not a certified test result.</p>',
    '    </div>',
    '  </section>',

    /* UNAVAILABLE */
    '  <section v-if="view===\'unavailable\'" class="view">',
    '    <p class="eyebrow">Not available</p>',
    '    <h1>This quiz is not ready yet</h1>',
    '    <p class="lede">{{ unavailableMessage }}</p>',
    '    <a v-if="demoAvailable" class="btn btn--primary" href="?demo=1">Try the local demo</a>',
    '    <div class="btn-row"><button class="btn btn--primary" type="button" @click="goHome">Back to topics</button></div>',
    '  </section>',

    '</main>',
    '<footer class="site-footer"><div class="wrap">',
    '  <p>DriveTest is a free practice tool. Sign artwork is a draft, photo-derived library and all records remain marked for verification; scores are for practice only and are not proof of driving competence.</p>',
    '  <p class="status">{{ dataStatus }}</p>',
    '</div></footer>',
  ].join("\n");

  var app = Vue.createApp({
    template: TEMPLATE,
    data: function () {
      return {
        isDemo: Boolean(demoQuestions),
        demoAvailable: document.getElementById("quiz-app").dataset.demoAvailable === "true",
        catalog: [],
        source: "api",
        loadError: "",
        ready: false,
        view: "home",
        quizLength: QUIZ_LENGTH,
        mascot: MASCOT,
        unavailableMessage: "There are no reviewed questions for that topic yet.",
        topics: [],
        quiz: { topicId: null, topicLabel: "", questions: [], index: 0, selections: [], checked: [], correct: [] },
        result: null,
        reviewOpen: false,
        shareStatus: "",
        shared: null,
      };
    },
    computed: {
      current: function () {
        return this.quiz.questions[this.quiz.index] || null;
      },
      currentSelection: function () {
        return this.quiz.selections[this.quiz.index] || [];
      },
      isChecked: function () {
        return !!this.quiz.checked[this.quiz.index];
      },
      lastWasCorrect: function () {
        return !!this.quiz.correct[this.quiz.index];
      },
      isLast: function () {
        return this.quiz.index + 1 >= this.quiz.questions.length;
      },
      canCheck: function () {
        return this.currentSelection.length > 0;
      },
      progressPct: function () {
        if (!this.quiz.questions.length) {
          return 0;
        }
        return Math.round((this.quiz.index / this.quiz.questions.length) * 100);
      },
      sharedPct: function () {
        if (!this.shared || !this.shared.n) {
          return 0;
        }
        return Math.round((this.shared.s / this.shared.n) * 100);
      },
      reviewItems: function () {
        var self = this;
        return this.quiz.questions.map(function (q, i) {
          return {
            prompt: q.prompt,
            correct: self.quiz.correct[i],
            your: self.quiz.selections[i].map(function (id) {
              return self.labelFor(q, id);
            }).join(", "),
            correctLabels: q.correctIds.map(function (id) {
              return self.labelFor(q, id);
            }).join(", "),
            explanation: q.explanation,
          };
        });
      },
      dataStatus: function () {
        if (this.isDemo) {
          return "Local sample questions; no database content was changed.";
        }
        if (!this.ready) {
          return "Loading questions…";
        }
        if (!this.catalog.length) {
          return this.loadError || "No questions could be loaded.";
        }
        return "Questions: " + this.catalog.length + " sign(s) from the API.";
      },
    },
    methods: {
      practiceLabel: practiceLabel,
      apiSignToCatalog: function (item) {
        var cls = item["class"] || null;
        var sub = item.subcategory || null;
        return {
          id: item.id,
          name: item.name,
          classCode: cls ? cls.code : null,
          classLabel: cls ? cls.name : null,
          subcategoryId: sub ? sub.id : null,
          subcategoryLabel: sub ? sub.name : null,
          meaning: item.meaning || "",
          image: API + "/signs/" + encodeURIComponent(item.id) + "/image",
        };
      },
      fetchCatalog: async function () {
        var collected = [];
        var page = 1;
        var lastPage = 1;
        do {
          var res = await fetch(API + "/signs?per_page=100&page=" + page, { headers: { Accept: "application/json" } });
          if (!res.ok) {
            throw new Error("API responded " + res.status);
          }
          var body = await res.json();
          collected = collected.concat((body.data || []).map(this.apiSignToCatalog));
          lastPage = (body.meta && body.meta.last_page) || 1;
          page++;
        } while (page <= lastPage && page <= 5);
        return collected;
      },
      buildTopics: function () {
        var self = this;
        this.topics = TOPICS.map(function (t) {
          var count = t.id === "mixed"
            ? Math.min(QUIZ_LENGTH, self.catalog.length)
            : Math.min(QUIZ_LENGTH, eligibleSigns(self.catalog, t.id).length);
          return { id: t.id, name: t.name, desc: t.desc, count: count };
        });
      },
      goHome: function () {
        if (this.isDemo) {
          this.startQuiz("demo");
          return;
        }
        this.view = "home";
        this.scrollTop();
      },
      scrollTop: function () {
        window.scrollTo({ top: 0 });
      },
      startQuiz: function (topicId) {
        var topic = TOPICS.filter(function (t) {
          return t.id === topicId;
        })[0];
        var questions = this.isDemo ? demoQuestions : buildQuiz(this.catalog, topicId);
        if (!questions.length) {
          this.unavailableMessage = "There are no questions for that topic yet. Pick another topic.";
          this.view = "unavailable";
          this.scrollTop();
          return;
        }
        this.quiz = {
          topicId: topicId,
          topicLabel: this.isDemo ? "Local demo" : (topic ? topic.name : topicId),
          questions: questions,
          index: 0,
          selections: questions.map(function () {
            return [];
          }),
          checked: questions.map(function () {
            return false;
          }),
          correct: questions.map(function () {
            return false;
          }),
        };
        this.result = null;
        this.reviewOpen = false;
        this.shareStatus = "";
        this.view = "quiz";
        this.scrollTop();
        this.focusOptions();
      },
      focusOptions: function () {
        var self = this;
        this.$nextTick(function () {
          var first = self.$refs.optionsEl && self.$refs.optionsEl.querySelector("input");
          if (first) {
            first.focus();
          }
        });
      },
      isChosen: function (optId) {
        return this.currentSelection.indexOf(optId) !== -1;
      },
      choose: function (optId, multi) {
        if (this.isChecked) {
          return;
        }
        var sel = this.currentSelection.slice();
        if (multi) {
          var at = sel.indexOf(optId);
          if (at === -1) {
            sel.push(optId);
          } else {
            sel.splice(at, 1);
          }
        } else {
          sel = [optId];
        }
        this.quiz.selections.splice(this.quiz.index, 1, sel);
      },
      optionClass: function (opt) {
        if (!this.isChecked) {
          return "";
        }
        var good = this.current.correctIds.indexOf(opt.id) !== -1;
        var chosen = this.isChosen(opt.id);
        if (good) {
          return "is-correct";
        }
        if (chosen) {
          return "is-wrong";
        }
        return "";
      },
      markFor: function (optId) {
        if (!this.isChecked) {
          return "";
        }
        if (this.current.correctIds.indexOf(optId) !== -1) {
          return "Correct answer";
        }
        if (this.isChosen(optId)) {
          return "Your choice";
        }
        return "";
      },
      labelFor: function (q, id) {
        var found = q.options.filter(function (o) {
          return o.id === id;
        })[0];
        return found ? found.label : id;
      },
      checkAnswer: function () {
        if (this.isChecked || !this.canCheck) {
          return;
        }
        var q = this.current;
        var sel = this.currentSelection.slice();
        this.quiz.correct.splice(this.quiz.index, 1, sameSet(sel, q.correctIds));
        this.quiz.checked.splice(this.quiz.index, 1, true);
      },
      nextQuestion: function () {
        if (this.isLast) {
          this.showResults();
          return;
        }
        this.quiz.index++;
        this.focusOptions();
        this.scrollTop();
      },
      showResults: function () {
        var total = this.quiz.questions.length;
        var score = this.quiz.correct.filter(Boolean).length;
        this.result = {
          topicId: this.quiz.topicId,
          topicLabel: this.quiz.topicLabel,
          score: score,
          total: total,
          pct: total ? Math.round((score / total) * 100) : 0,
        };
        this.reviewOpen = false;
        this.shareStatus = "";
        this.view = "results";
        this.scrollTop();
      },
      toggleReview: function () {
        this.reviewOpen = !this.reviewOpen;
      },
      encodeResult: function (payload) {
        var json = JSON.stringify(payload);
        return btoa(unescape(encodeURIComponent(json))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
      },
      decodeResult: function (value) {
        try {
          var b64 = value.replace(/-/g, "+").replace(/_/g, "/");
          while (b64.length % 4) {
            b64 += "=";
          }
          return JSON.parse(decodeURIComponent(escape(atob(b64))));
        } catch (error) {
          return null;
        }
      },
      buildShareUrl: function () {
        var r = this.result;
        var payload = { v: 1, t: r.topicId, ti: r.topicLabel, s: r.score, n: r.total };
        var url = new URL(window.location.href);
        url.search = "?r=" + this.encodeResult(payload);
        url.hash = "";
        return url.toString();
      },
      shareResult: async function () {
        var r = this.result;
        var url = this.buildShareUrl();
        var text = "I scored " + r.score + "/" + r.total + " on DriveTest " + practiceLabel(r.topicLabel) + ".";
        try {
          if (navigator.share) {
            await navigator.share({ title: "DriveTest score", text: text, url: url });
            this.shareStatus = "Shared.";
            return;
          }
          await navigator.clipboard.writeText(text + " " + url);
          this.shareStatus = "Link copied to your clipboard.";
        } catch (error) {
          this.shareStatus = "Copy this link: " + url;
        }
      },
      init: async function () {
        if (this.isDemo) {
          this.ready = true;
          this.startQuiz("demo");
          return;
        }
        var params = new URLSearchParams(window.location.search);
        var shared = params.get("r") ? this.decodeResult(params.get("r")) : null;
        try {
          this.catalog = await this.fetchCatalog();
          this.source = "api";
        } catch (error) {
          this.catalog = [];
          this.loadError = "Could not reach the sign API. " + error.message;
        }
        this.ready = true;
        this.buildTopics();

        if (shared && typeof shared.s === "number") {
          this.shared = shared;
          this.view = "shared";
          return;
        }
        if (!this.catalog.length) {
          this.unavailableMessage = this.loadError || "No published signs are available yet.";
          this.view = "unavailable";
          return;
        }
        this.view = "home";
      },
    },
    mounted: function () {
      this.init();
    },
  });

  app.mount("#quiz-app");
})();
