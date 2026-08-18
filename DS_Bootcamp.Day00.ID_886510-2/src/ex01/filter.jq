["id", "created_at", "name", "has_test", "alternate_url"],  # CSV sarlavhalar
(.items[] | [ .id, .created_at, .name, .has_test, .alternate_url ])
| @csv
