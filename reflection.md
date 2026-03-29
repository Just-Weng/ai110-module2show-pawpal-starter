# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

![Initial](UML-Initial.png)
The Pawpal initial UML takes in a Pet object to create pet tasks, each task will have a priority as well as details to schedule the task. The scheduled task willl have timeslots for how long the task will take.

**b. Design changes**

![](<UML-Version-1.png>)
My UML did change, but before implementation. I realized that there needed to be a separate class that handled the scheduling due to priorities for certain tasks when I was designing the UML.


---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
The scheduler considers the shortest time first, to complete the most within a given period.
- How did you decide which constraints mattered most?
I decided that the most efficient way to complete the most tasks was important, so I prioritized that.
**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
A tradeoff that the scheduler makes is that if it considers time first, it wont reflect how important an task is as an result.
- Why is that tradeoff reasonable for this scenario?
This is a reasonable tradeoff because the amount of tasks completed within a given time is very efficient.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?
I used AI for brainstorming what I could use for the different activities. I found that prompts that were most helpful was asking what are some basic functionalities that I should consider for the given task.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?
The UML was one moment when I did not accept the AI suggestion as is, it did not specifically have a class for the Scheduler which would use the scheduled tasks and order them. 
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
The features that I tested were if recurring tasks were added after completed, sorting by task time, time conflicts between tasks, filtering task.
- Why were these tests important?
They were important because recurring tasks was done to ensure adding tasks back in did not mess up the table for tasks, as for the others, the tests were done to ensure proper function.

**b. Confidence**

- How confident are you that your scheduler works correctly?
Fairly confident, plan generation properly sorted the lowest task first when adding multiple tasks.
- What edge cases would you test next if you had more time?
some edge cases are making sure that the recurring tasks keep getting tested for new accepting of recurring tasks. 
---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
How the UI turned out, it looked very minial and stylish.
**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
some of the algorithms did not apply properly but most features worked well enough.
**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
I learned that there needs to be a lot of scrutiny over generation in which it was not fully accurate. I also realize how quickly code builds up and how there needs to be a focus to start bottom up to ensure it doesnt become spaghetti code.