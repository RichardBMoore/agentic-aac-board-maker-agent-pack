# Teacher Guide: Try An Activity Inside QLearn (SCORM)

**Goal:** a student opens a QLearn lesson and uses the accessible activity right there, without downloading a file. This first test checks whether QLearn's SCORM player runs our activity properly. Do it in a **sandbox course with no students**.

**You need:** the `.scorm12.zip` file the agent built (keep it zipped), plus the backup `.split.scorm12.zip`. About 15 minutes.

## Upload (5 minutes)

1. Open your sandbox course. In the course menu, click **SCORM**. A crossed-out eye beside it is fine: students can't see the link, but you can use it. If there's no SCORM link, go to **Settings → Navigation**; if SCORM isn't listed at all, it isn't enabled for the course, so ask your QLearn administrator.
2. Click **Upload**, choose the `.scorm12.zip` file (not an unzipped folder) and click **Open**.
3. When it finishes, open **Choose Import Type**, pick **Import as page** and click **Go**. You can't change this choice later.
4. Go to **Pages** and find the new page. **Check whether it says Published.** If it does, unpublish it while you test.

## Check it as the teacher (5 minutes)

5. Open the page. You should see the activity's **Start board / Full screen / Sound check** buttons inside the page.
6. Click **Sound check**, then **Start board**. Click a symbol: it should speak and show the message.
7. Rest the mouse still on a symbol for about a second. It should fill up and speak once, and moving away early should cancel it.
8. Click inside the activity once, then try **Tab** and **Enter**.
9. Reload and press **Full screen**. Write down whether it opened or said "Full screen was blocked". Blocked is a result, not a failure: the board should still work.

**If the activity area is blank or looks unstyled:** QLearn is blocking the activity's built-in scripts. Upload the **`.split.scorm12.zip`** as a new page (steps 2–4) and test again. Delete the blank one from the SCORM tool afterwards.

## Check it as a student (3 minutes)

10. **Settings → Student View**, open the page and repeat steps 6–9. Then **Leave Student View**. (The test student is not a real student.)

## Later, with the team: the student's device

Only once the checks above work. With the student's AAC/OT/SLP team, try it on the student's own Accent or device, with their real access method (eye gaze, touch or switch) and the way they normally reach QLearn. How the student gets access (publishing, modules, who it's assigned to) is your decision. The agent never publishes.

## Results sheet

| Check | Result | Notes |
| --- | --- | --- |
| Date / course (sandbox?) | | |
| Uploaded without error? (copy any error text) | | |
| Imported as page? Page published or unpublished at first? | | |
| Activity appears inside the page? | | |
| Which package worked: normal or split? | | |
| Speech: Sound check heard? Voice name/quality? | | |
| Click/touch selects once and speaks? | | |
| Mouse dwell (~1 s) selects once; moving away cancels? | | |
| Stop speech works? | | |
| Tab + Enter work after clicking into the activity? | | |
| Full screen: opened or "blocked"? | | |
| Fits without scrolling or cut-off buttons? Screen/browser size? | | |
| Student View: same results? | | |
| Any error messages (F12 → Console, optional)? | | |
| Device trial: device model, NuVoice or Empower, Windows scaling % | | |
| Device trial: eye-gaze dwell works? OS dwell-click works? | | |
| Microphone/dictation needed? Tried? Result? | | |
| Student and team comments | | |

Give the agent the filled-in sheet. It decides the next step: keep the normal package, switch to split, or ask the QLearn administrator about "Load in a new tab" or another approved route.

## Good to know

- Nothing in the activity sends the student's choices or messages to QLearn. The package only tells QLearn it was opened and closed.
- To update an activity, upload the new ZIP as a new import, check it, then delete the old one **from the SCORM tool**. Deleting there removes it everywhere in the course.
- The symbols are ARASAAC pictograms (CC BY-NC-SA). The licence file travels inside the package.
