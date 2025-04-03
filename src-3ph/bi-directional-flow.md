
## Understanding Bi-Directional Power Flow in Revenue Meter Data

When a revenue meter records **nonzero values for both `kw_del` and `kw_rec`** during the same 15-minute interval, it indicates **power flow reversal** occurred within that time block.

---

### 🔁 Example

```text
Start Time: 07/12/24 11:00:00  
kw_del = 0.84  
kw_rec = 55.79
```

| meter     | Record No. | Event Type | Start Time         | End Time           | kw_del | kw_rec | kva_del | kva_rec | MW_del   | MW_rec   | MVA_del  | MVA_rec  | MW_net  | MVA_net | PF_net  |
|-----------|------------|------------|--------------------|--------------------|--------|--------|---------|---------|----------|----------|----------|----------|---------|---------|---------|
| 144800052 | 157594     | Normal     | 07/12/24 11:00:00  | 07/12/24 11:15:00  | 0.84   | 55.79  | 15.02   | 228.51  | 0.024192 | 1.606752 | 0.432576 | 6.581088 | 1.630944| 7.013664| 0.232538 |
| 144800052 | 157595     | Normal     | 07/12/24 11:15:00  | 07/12/24 11:30:00  | 2.45   | 15.01  | 46.47   | 126.19  | 0.07056  | 0.432288 | 1.338336 | 3.634272 | 0.502848| 4.972608| 0.101124 |
| 144800052 | 157596     | Normal     | 07/12/24 11:30:00  | 07/12/24 11:45:00  | 11.55  | 4.97   | 98.57   | 35.42   | 0.33264  | 0.143136 | 2.838816 | 1.020096 | 0.475776| 3.858912| 0.123293 |
| 144800052 | 157597     | Normal     | 07/12/24 11:45:00  | 07/12/24 12:00:00  | 33.89  | 0.53   | 199.48  | 1.19    | 0.976032 | 0.015264 | 5.745024 | 0.034272 | 0.991296| 5.779296| 0.171525 |
| 144800052 | 157598     | Normal     | 07/12/24 12:00:00  | 07/12/24 12:15:00  | 41.46  | 0.04   | 230.86  | 0.01    | 1.194048 | 0.001152 | 6.648768 | 0.000288 | 1.1952  | 6.649056| 0.179755 |
| 144800052 | 157599     | Normal     | 07/12/24 12:15:00  | 07/12/24 12:30:00  | 39.12  | 0.05   | 229.31  | 0.22    | 1.126656 | 0.00144  | 6.604128 | 0.006336 | 1.128096| 6.610464| 0.170653 |
| 144800052 | 157600     | Normal     | 07/12/24 12:30:00  | 07/12/24 12:45:00  | 34.01  | 0.07   | 214.15  | 0.07    | 0.979488 | 0.002016 | 6.16752  | 0.002016 | 0.981504| 6.169536| 0.159089 |
| 144800052 | 157601     | Normal     | 07/12/24 12:45:00  | 07/12/24 13:00:00  | 41.42  | 0.02   | 228.21  | 0.08    | 1.192896 | 0.000576 | 6.572448 | 0.002304 | 1.193472| 6.574752| 0.181524 |


This means:
- **0.84 kWh** were delivered **to the site** (meter → load)
- **55.79 kWh** were received **from the site** (load → grid, e.g., solar export)

---

### ⚙️ Why This Happens

This condition is **normal** in systems with:
- **Solar PV**, where production can temporarily exceed local demand
- **Battery energy storage systems (BESS)** that charge and discharge dynamically

The meter accumulates **total forward and reverse energy** over the interval — it does not sample direction second-by-second.

Even a brief moment of power reversal during the 15-minute block results in **both `kw_del` and `kw_rec` > 0**.

---

### 📊 Power Factor Impact

For example:

```text
MW_net  = 1.630944  
MVA_net = 7.013664  
PF_net  = 0.232538
```

- A **low `PF_net`** occurs when the real power (`MW_net`) is small compared to apparent power (`MVA_net`).
- This often happens when there's **both forward and reverse flow** in the same block.

---

### 🧠 Interpreting the Pattern

| Interval Start | kw_del | kw_rec | Notes                        |
|----------------|--------|--------|------------------------------|
| 11:00          | 0.84   | 55.79  | Heavy export                 |
| 11:15          | 2.45   | 15.01  | Export decreasing            |
| 11:30          | 11.55  | 4.97   | Shifting toward consumption  |
| 11:45 onward   | 33.89+ | ~0     | Forward flow resumes         |

This pattern could suggest:
- Solar generation **dropping off**
- A load (e.g. HVAC) **turning on**
- **Clouds** moving over PV panels

---

### ✅ Key Takeaway

Meters that record both `kw_del` and `kw_rec` in a time block are:
- Accurately capturing **bidirectional flow**
- Showing that **reversal occurred during that interval**
- **Not in error** — this is an expected result in DER systems

Use this data to analyze:
- **Solar export behavior**
- **DER ramping**
- **Grid support or backfeed scenarios**
