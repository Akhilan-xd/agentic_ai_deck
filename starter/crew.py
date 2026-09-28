"""Crew definition. Add agents and tasks here, and describe them in config/."""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, llm, task, tool

from starter.llm import local_llm
from starter.tools.example_tool import WordCountTool


@CrewBase
class StarterCrew:
    """Two-agent crew: research a topic, then write a short brief."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @llm
    def local(self):
        return local_llm()

    @tool
    def word_count(self):
        return WordCountTool()

    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config["researcher"])

    @agent
    def writer(self) -> Agent:
        return Agent(config=self.agents_config["writer"])

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config["research_task"])

    @task
    def write_task(self) -> Task:
        return Task(config=self.tasks_config["write_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
