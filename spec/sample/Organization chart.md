---
title: Organization chart

---

---
config:
  layout: dagre
---
```mermaid
flowchart LR
 subgraph team1["team1"]
        sub1["sub1"]
        Lead["Lead"]
        sub2["sub2"]
  end
 subgraph team2["team2"]
        sub3["sub3"]
        Lead1["Lead1"]
        sub4["sub4"]
  end
    Head["Head"] --- Lead & Lead1
    Lead --- sub1 & sub2
    Lead1 --- sub3 & sub4
```