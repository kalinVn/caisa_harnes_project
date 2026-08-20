ai-harness/
│
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── config/
│   ├── harness/
│   │   └── HARNESS.md
│   ├── agents/
│   │   └── AGENTS.md
│   ├── rules/
│   │   └── RULES.md
│   ├── tools/
│   │   └── TOOLS.md
│   └── workflows/
│       └── WORKFLOWS.md
│
├── src/
│   └── harness/
│
│       ├── application/
│       │
│       │   ├── entrypoints/
│       │   │
│       │   │   ├── cli/
│       │   │   │   ├── commands/
│       │   │   │   │   └── handler.py
│       │   │   │   ├── input/
│       │   │   │   │   └── reader.py
│       │   │   │   └── output/
│       │   │   │       └── writer.py
│       │   │   │
│       │   │   └── api/
│       │   │       ├── routes/
│       │   │       │   └── router.py
│       │   │       ├── requests/
│       │   │       │   └── parser.py
│       │   │       └── responses/
│       │   │           └── builder.py
│       │   │
│       │   └── orchestration/
│       │
│       │       ├── engine/
│       │       │
│       │       │   ├── runner/
│       │       │   │   └── runner.py
│       │       │   │
│       │       │   ├── loop/
│       │       │   │   └── loop.py
│       │       │   │
│       │       │   └── lifecycle/
│       │       │       └── lifecycle.py
│       │       │
│       │       ├── state/
│       │       │
│       │       │   ├── session/
│       │       │   │   └── state.py
│       │       │   │
│       │       │   └── task/
│       │       │       └── state.py
│       │       │
│       │       └── routing/
│       │
│       │           ├── dispatcher/
│       │           │   └── dispatcher.py
│       │           │
│       │           └── resolver/
│       │               └── resolver.py
│       │
│       ├── intelligence/
│       │
│       │   ├── agents/
│       │   │
│       │   │   ├── base/
│       │   │   │
│       │   │   │   ├── contract/
│       │   │   │   │   └── contract.py
│       │   │   │   ├── state/
│       │   │   │   │   └── state.py
│       │   │   │   └── lifecycle/
│       │   │   │       └── lifecycle.py
│       │   │   │
│       │   │   ├── coding/
│       │   │   │
│       │   │   │   ├── runner/
│       │   │   │   │   └── runner.py
│       │   │   │   ├── planner/
│       │   │   │   │   └── planner.py
│       │   │   │   └── instructions/
│       │   │   │       └── loader.py
│       │   │   │
│       │   │   ├── review/
│       │   │   │
│       │   │   │   ├── runner/
│       │   │   │   │   └── runner.py
│       │   │   │   ├── analyzer/
│       │   │   │   │   └── analyzer.py
│       │   │   │   └── findings/
│       │   │   │       └── builder.py
│       │   │   │
│       │   │   ├── testing/
│       │   │   │
│       │   │   │   ├── runner/
│       │   │   │   │   └── runner.py
│       │   │   │   ├── planner/
│       │   │   │   │   └── planner.py
│       │   │   │   └── verifier/
│       │   │   │       └── verifier.py
│       │   │   │
│       │   │   ├── debugging/
│       │   │   │
│       │   │   │   ├── runner/
│       │   │   │   │   └── runner.py
│       │   │   │   ├── diagnosis/
│       │   │   │   │   └── diagnosis.py
│       │   │   │   └── repair/
│       │   │   │       └── repair.py
│       │   │   │
│       │   │   └── architect/
│       │   │
│       │   │       ├── runner/
│       │   │       │   └── runner.py
│       │   │       ├── planner/
│       │   │       │   └── planner.py
│       │   │       └── decisions/
│       │   │           └── decisions.py
│       │   │
│       │   ├── models/
│       │   │
│       │   │   ├── contracts/
│       │   │   │
│       │   │   │   ├── model/
│       │   │   │   │   └── contract.py
│       │   │   │   ├── request/
│       │   │   │   │   └── model.py
│       │   │   │   └── response/
│       │   │   │       └── model.py
│       │   │   │
│       │   │   ├── routing/
│       │   │   │
│       │   │   │   ├── router/
│       │   │   │   │   └── router.py
│       │   │   │   ├── selector/
│       │   │   │   │   └── selector.py
│       │   │   │   ├── strategy/
│       │   │   │   │   └── strategy.py
│       │   │   │   └── fallback/
│       │   │   │       └── fallback.py
│       │   │   │
│       │   │   └── providers/
│       │   │
│       │   │       ├── openai/
│       │   │       │   ├── client/
│       │   │       │   │   └── client.py
│       │   │       │   ├── mapping/
│       │   │       │   │   └── mapper.py
│       │   │       │   └── tools/
│       │   │       │       └── mapper.py
│       │   │       │
│       │   │       ├── anthropic/
│       │   │       │   ├── client/
│       │   │       │   │   └── client.py
│       │   │       │   ├── mapping/
│       │   │       │   │   └── mapper.py
│       │   │       │   └── tools/
│       │   │       │       └── mapper.py
│       │   │       │
│       │   │       ├── google/
│       │   │       │   ├── client/
│       │   │       │   │   └── client.py
│       │   │       │   └── mapping/
│       │   │       │       └── mapper.py
│       │   │       │
│       │   │       └── local/
│       │   │           ├── client/
│       │   │           │   └── client.py
│       │   │           └── mapping/
│       │   │               └── mapper.py
│       │   │
│       │   └── context/
│       │
│       │       ├── building/
│       │       │   ├── builder/
│       │       │   │   └── builder.py
│       │       │   ├── instructions/
│       │       │   │   └── loader.py
│       │       │   └── messages/
│       │       │       └── builder.py
│       │       │
│       │       ├── retrieval/
│       │       │   ├── files/
│       │       │   │   └── retriever.py
│       │       │   ├── memory/
│       │       │   │   └── retriever.py
│       │       │   └── search/
│       │       │       └── retriever.py
│       │       │
│       │       ├── compression/
│       │       │   ├── summarizer/
│       │       │   │   └── summarizer.py
│       │       │   └── budget/
│       │       │       └── manager.py
│       │       │
│       │       └── window/
│       │           ├── manager/
│       │           │   └── manager.py
│       │           └── tokens/
│       │               └── counter.py
│       │
│       ├── execution/
│       │
│       │   ├── tools/
│       │   │
│       │   │   ├── registry/
│       │   │   │   ├── registration/
│       │   │   │   │   └── registry.py
│       │   │   │   └── schemas/
│       │   │   │       └── schema.py
│       │   │   │
│       │   │   ├── filesystem/
│       │   │   │   ├── read/
│       │   │   │   │   └── tool.py
│       │   │   │   ├── write/
│       │   │   │   │   └── tool.py
│       │   │   │   ├── edit/
│       │   │   │   │   └── tool.py
│       │   │   │   └── search/
│       │   │   │       └── tool.py
│       │   │   │
│       │   │   ├── shell/
│       │   │   │   ├── execution/
│       │   │   │   │   └── tool.py
│       │   │   │   └── result/
│       │   │   │       └── model.py
│       │   │   │
│       │   │   ├── git/
│       │   │   │   ├── diff/
│       │   │   │   │   └── tool.py
│       │   │   │   ├── status/
│       │   │   │   │   └── tool.py
│       │   │   │   ├── commit/
│       │   │   │   │   └── tool.py
│       │   │   │   └── history/
│       │   │   │       └── tool.py
│       │   │   │
│       │   │   └── testing/
│       │   │       ├── runner/
│       │   │       │   └── tool.py
│       │   │       └── result/
│       │   │           └── model.py
│       │   │
│       │   └── workflows/
│       │
│       │       ├── code_review/
│       │       │   ├── start/
│       │       │   │   └── step.py
│       │       │   ├── inspect/
│       │       │   │   └── step.py
│       │       │   ├── review/
│       │       │   │   └── step.py
│       │       │   └── finish/
│       │       │       └── step.py
│       │       │
│       │       ├── feature/
│       │       │   ├── analyze/
│       │       │   │   └── step.py
│       │       │   ├── plan/
│       │       │   │   └── step.py
│       │       │   ├── implement/
│       │       │   │   └── step.py
│       │       │   └── verify/
│       │       │       └── step.py
│       │       │
│       │       └── debugging/
│       │           ├── inspect/
│       │           │   └── step.py
│       │           ├── diagnose/
│       │           │   └── step.py
│       │           ├── repair/
│       │           │   └── step.py
│       │           └── verify/
│       │               └── step.py
│       │
│       ├── infrastructure/
│       │
│       │   ├── memory/
│       │   │   ├── session/
│       │   │   │   ├── reader/
│       │   │   │   │   └── reader.py
│       │   │   │   └── writer/
│       │   │   │       └── writer.py
│       │   │   ├── project/
│       │   │   │   ├── reader/
│       │   │   │   │   └── reader.py
│       │   │   │   └── writer/
│       │   │   │       └── writer.py
│       │   │   └── persistence/
│       │   │       ├── store/
│       │   │       │   └── store.py
│       │   │       └── cache/
│       │   │           └── cache.py
│       │   │
│       │   ├── security/
│       │   │   ├── permissions/
│       │   │   │   ├── checker/
│       │   │   │   │   └── checker.py
│       │   │   │   └── rules/
│       │   │   │       └── rules.py
│       │   │   └── approvals/
│       │   │       ├── request/
│       │   │       │   └── request.py
│       │   │       └── decision/
│       │   │           └── decision.py
│       │   │
│       │   └── observability/
│       │       ├── logging/
│       │       │   ├── logger/
│       │       │   │   └── logger.py
│       │       │   └── events/
│       │       │       └── events.py
│       │       ├── tracing/
│       │       │   ├── tracer/
│       │       │   │   └── tracer.py
│       │       │   └── spans/
│       │       │       └── spans.py
│       │       └── metrics/
│       │           ├── collector/
│       │           │   └── collector.py
│       │           └── usage/
│       │               └── usage.py
│       │
│       └── domain/
│           ├── messages/
│           │   ├── message/
│           │   │   └── model.py
│           │   └── role/
│           │       └── model.py
│           ├── tasks/
│           │   ├── task/
│           │   │   └── model.py
│           │   └── status/
│           │       └── model.py
│           ├── tool_calls/
│           │   ├── call/
│           │   │   └── model.py
│           │   └── result/
│           │       └── model.py
│           └── sessions/
│               ├── session/
│               │   └── model.py
│               └── state/
│                   └── model.py
│
├── prompts/
│   ├── system/
│   ├── agents/
│   └── workflows/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evals/
│
├── scripts/
│
└── data/
    ├── memory/
    ├── logs/
    └── cache/