# Rules

We have very precise rules over how our Git commit messages must be formatted.
This format leads to **easier to read commit history** and makes it analyzable for changelog generation.

## Commit Message

```
<type>: <short summary>
  │       │
  │       └─⫸ Summary in present tense.
  │
  └─⫸ Commit Type: build|ci|docs|fix|perf|refactor|test
```

The `<type>` and `<short summary>` fields are mandatory.


### Type

Must be one of the following:

| Type         | Description                                                                                         |
|--------------|-----------------------------------------------------------------------------------------------------|
| **build**    | Changes that affect external dependencies |
| **ci**       | Changes to our CI configuration files and scripts (examples: Github Actions)                        |
| **docs**     | Documentation only changes                                                                          |
| **fix**      | A bug fix                                                                                           |
| **perf**     | A code change that improves performance                                                             |
| **refactor** | A code change that neither fixes a bug nor adds a feature                                           |
| **test**     | Adding missing tests or correcting existing tests                                                   |


### Short Summary

Use the summary field to provide a succinct description of the change:

* use the imperative, present tense: "change" not "changed" nor "changes"
* don't capitalize the first letter
* no dot (.) at the end


## Description

Just as in the summary, use the imperative, present tense: "fix" not "fixed" nor "fixes".

Explain the motivation for the change in the commit message body. This commit message should explain _why_ you are making the change.
You can include a comparison of the previous behavior with the new behavior in order to illustrate the impact of the change.