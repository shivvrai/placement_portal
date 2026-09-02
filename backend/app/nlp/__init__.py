"""
NLP package — resume parsing, skill extraction, taxonomy matching, JD parsing.

Modules:
  resume_parser   — extract raw text from PDF / DOCX / TXT
  skill_extractor — detect skill mentions in free-form text
  taxonomy_matcher — fuzzy-match raw skills to canonical Skill DB records
  jd_parser       — parse job descriptions for structured fields
  pipeline        — end-to-end orchestration (resume -> StudentSkills)
"""
