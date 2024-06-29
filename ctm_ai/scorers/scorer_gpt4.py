from typing import Any, List

from openai import OpenAI

from ..utils import logprobs_to_softmax, score_exponential_backoff
from .scorer_base import BaseScorer


@BaseScorer.register_scorer('gpt4_scorer')
class GPT4Scorer(BaseScorer):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.init_scorer()

    def init_scorer(self) -> None:
        self.scorer = OpenAI()

    @score_exponential_backoff(retries=5, base_wait_time=1)
    def ask_relevance(self, query: str, gists: List[str]) -> float:
        gist = gists[0]
        response = self.scorer.chat.completions.create(
            model='gpt-4-0125-preview',
            messages=[
                {
                    'role': 'user',
                    'content': f"Is the information ({gist}) related with the query ({query})? Answer with 'Yes' or 'No'.",
                }
            ],
            max_tokens=50,
            logprobs=True,
            top_logprobs=20,
        )
        if (
            response.choices
            and response.choices[0].logprobs
            and response.choices[0].logprobs.content
            and response.choices[0].logprobs.content[0]
            and response.choices[0].logprobs.content[0].top_logprobs
        ):
            top_logprobs = response.choices[0].logprobs.content[0].top_logprobs
            logprob_dict = {logprob.token: logprob.logprob for logprob in top_logprobs}
            probs = logprobs_to_softmax(
                [logprob_dict.get('Yes', 0), logprob_dict.get('No', 0)]
            )
            return probs[0]
        else:
            return 0.0
