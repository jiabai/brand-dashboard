export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      ['feat', 'fix', 'docs', 'chore', 'refactor', 'test', 'build', 'ci', 'perf', 'revert']
    ],
    'subject-empty': [2, 'never'],
    'header-max-length': [2, 'always', 200]
  }
}

