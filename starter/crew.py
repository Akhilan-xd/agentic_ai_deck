# wires the agents and tasks from the yaml files

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, llm, task, tool

from starter.llm import local_llm
from starter.tools.example_tool import WordCountTool
from starter.tools.whitespace import WhitespaceTool


@CrewBase
class StarterCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @llm
    def local(self):
        return local_llm()

    @tool
    def word_count(self):
        return WordCountTool()

    @tool
    def whitespace_tool(self):
        return WhitespaceTool()

    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config["researcher"])

    @agent
    def writer(self) -> Agent:
        return Agent(config=self.agents_config["writer"])

    @agent
    def editor(self) -> Agent:
        return Agent(config=self.agents_config["editor"])

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config["research_task"])

    @task
    def write_task(self) -> Task:
        return Task(config=self.tasks_config["write_task"])

    @task
    def edit_task(self) -> Task:
        return Task(config=self.tasks_config["edit_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
