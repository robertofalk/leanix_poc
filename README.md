# LeanIX

## Task Description

At LeanIX we currently have a research team that takes existing data within our systems and enriches it with more information. The goal is to automate this process.
When you get the name of an Application or IT component, try to enrich it with certain details about it, like:
Description
Provider
Lifecycle (think "end of life")
Afterwards consider a few topics:
How would you make sure to keep this information up to date in the long run (e.g. reflect changed lifecycle, renaming of the product etc.)
How would you test & measure the accuracy of the solution
Please submit your solution at least two business days before the interview. You can do so by sharing it via private GitHub repository. The task is meant to take a reasonable amount of time, so please consider that as you prepare it and either discuss any questions with me, let the Talent Acquisition team know if you need more time or make appropriate tradeoffs.

## Solution
The proposed solution is to use a Large Language Model (LLM) to generate the descriptions, provider, and lifecycle based on a reliable data source. The key aspects of this solution are determining the appropriate data source and designing a pipeline to feed information to the LLM for summarization. Additionally, mechanisms for regular updates and accuracy measurement must be established.

### Assumptions
- The input data is always valid.

### Data Source
Using Google as a data source is unreliable due to inconsistent information sources and the potential for loading data from unofficial or incorrect documents. Instead, Wikipedia is proposed as a generic and (somewhat) reliable source of truth, assuming that the articles are well-maintained and regularly updated.

### LLM
We need an LLM to "read" information from the data source and extract the required data. Initially, the usage of an agent was considered since it could make decisions autonomously. However, since decisions at the LLM level are not required and to maintain control over the data source pipeline, I decided to use a completion with an embeddings pipeline.

## Implementation

The problem can be broken down into three main components:
1. Enrichment
2. Updates
3. Testing

### Enrichment
Enrichment is carried out using Wikipedia as the source. Based on the article, the LLM is prompted to create a concise summary of the item. This summary is then stored alongside the original text and key details such as provider and lifecycle information.

### Updates
On a regular basis, all items stored in the database are checked for changes. Using the Wikipedia article's `revision_id`, it is possible to verify if there have been any changes. If there are no changes, the summarization process is skipped entirely. This ensures that the database remains up to date without unnecessary reprocessing.

On a productive scenario, a more robust solution with a queue and async workers could be used to speed up and parallelize the work.

### Testing
Initially, BLEU (Bilingual Evaluation Understudy) and ROUGE (Recall Oriented Understudy for Gisting Evaluation) scores were considered to calculate similarity between the generated summary and the article. However, these scores mainly compare the number of matching words or combinations of words, which is not suitable for summaries. Since we are summarizing long texts into 1-2 paragraphs, both approaches return very low values due to the lack of overlap between the generated summary and the reference.

Instead, METEOR (Metric for Evaluation of Translation with Explicit ORdering) was chosen because it considers synonyms and semantic meaning, providing a more accurate measure of summarization quality. Although the difference in size between the generated summary and the original text still impacts the final metric, METEOR provides a more meaningful evaluation.

## TODO/Improvements
1. Implement a multi-source verification system where data is cross-checked among multiple sources before being accepted. Use reference links from Wikipedia as secondary data sources.
2. None of the metrics used for testing fully capture the performance for this particular problem. The significant size difference between the original text and the generated summary negatively influences the scores. Investigate domain-specific metrics that may better evaluate the summarization accuracy.

3. Add Retrieval Augmented Generation (RAG) to support larger Wikipedia articles.
   - Validate if the initial sections of the articles provide all necessary information or if RAG is required to process larger texts.

4. Establish a user interface for reviewing and editing summaries to ensure human oversight and maintain high-quality data.

5. Use a more sophisticated version control for each summary version to track and manage changes over time more efficiently.

