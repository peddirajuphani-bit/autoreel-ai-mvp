from abc import ABC, abstractmethod

class ContentProvider(ABC):
    @abstractmethod
    def generate(self, profile): ...

class MockContentProvider(ContentProvider):
    def generate(self, p):
        topic = f"5 practical AI skills for {p.target_audience}"
        hook = "Your next career advantage may not be another certificate."
        scenes = [
          ("Stop collecting certificates", "Your next career advantage may not be another certificate.", 4),
          ("Skill 1: Prompt clearly", "Learn to give AI clear context, constraints and examples.", 4),
          ("Skill 2: Verify outputs", "Always check facts, numbers and sources before using an AI answer.", 4),
          ("Skill 3: Automate workflows", "Connect AI to a repeatable work process, not just one-off questions.", 5),
          ("Skill 4: Protect data", "Never paste confidential company or candidate information into unapproved tools.", 5),
          ("Skill 5: Show outcomes", "Measure time saved, quality improved and business impact.", 4),
          ("Save this checklist", "Save this Reel and choose one skill to practise this week.", 4),
        ]
        script = " ".join(x[1] for x in scenes)
        return {
          "topic": topic, "hook": hook, "title": "5 AI Skills That Matter at Work",
          "script": script,
          "caption": "AI fluency is becoming a practical workplace skill. Start with one capability, use it responsibly, and measure the outcome.",
          "hashtags": "#AISkills #CareerGrowth #TechCareers #FutureOfWork #IndiaTech",
          "cover_text": "5 AI Skills You Need", "cta": "Save this and practise one skill this week.",
          "quality_score": 88, "scenes": scenes
        }

