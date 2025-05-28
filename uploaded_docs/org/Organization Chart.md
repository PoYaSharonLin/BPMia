---
title: Organization Chart

---

---
title: Organization Chart
---

```mermaid
flowchart LR

  subgraph HR["Human Resources"]
    Helen["Helen Chang\nHR Manager"]
  end

  subgraph Sales["Sales Department"]
    Jane["Jane Doe\nSales Manager"]
    Chris["Chris Lin\nSales Representative"]
    Anna["Anna Yu\nSales Representative"]
  end

  subgraph IT["Information Technology"]
    Mike["Michael Brown\nCRM Admin"]
  end

  subgraph Data["Data & Analytics"]
    Emily["Emily Wu\nData Analyst Team Lead"]
  end

  CEO["Alex Wang\nChief Executive Officer"]

  CEO --> Helen
  CEO --> Jane
  CEO --> Mike
  Jane --> Chris
  Jane --> Anna
  Jane --> Emily
```
