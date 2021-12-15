# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.0.0 - 2021-12-15
- Large refactor to make this easier to maintain later. Did I really need to do that? Probably not. But I hated staring at ~1000 lines of code in one file
- Made it easier to add new commands and events by extending base classes

## 0.0.1 - 2021-12-02
### Added
- All initial commands including:
- /verifyme <abc123>,<first_name>,<last_name>
- /tutors 
- /tutor <in|out> [message_in_quotes]
- /updatecourse [all]
- /updatelist
- /removeroles
- /removecourses
- /resetuser <abc123>
- /update [install]
