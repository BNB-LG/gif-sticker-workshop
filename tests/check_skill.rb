# Optional frontmatter validation using an existing Ruby/Psych installation.
require 'yaml'

root = File.expand_path('..', __dir__)
text = File.read(File.join(root, 'SKILL.md'))
match = text.match(/\A---\n(.*?)\n---\n/m)
abort 'Missing frontmatter' unless match
fields = YAML.safe_load(match[1])
abort 'Expected name and description only' unless fields.is_a?(Hash) && fields.keys.sort == %w[description name]
name = fields['name']
abort 'Invalid skill name' unless name.is_a?(String) && name.match?(/\A[a-z0-9]+(?:-[a-z0-9]+)*\z/) && name.length <= 64
description = fields['description']
abort 'Invalid description' unless description.is_a?(String) && !description.empty? && description.length <= 500 && !description.match?(/[<>]/)
abort 'Unfinished scaffold' if text.match?(/^\[TODO:/)
puts 'PASS: YAML frontmatter, fields, name, description and scaffold checks (Ruby Psych)'
