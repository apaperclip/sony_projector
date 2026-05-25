# Working with GitHub Copilot Coding Agent

This repository is already initialized as the Sony Projector integration. Do not ask Copilot to transform a generic blueprint; ask it to work within the current integration structure.

## Good Prompt Shape

Include:

- The projector behavior you want to add or fix
- Which protocol data is already available from `sony_projector_protocol`
- Relevant logs or packet/status examples
- Expected Home Assistant entity behavior
- Any breaking-change concerns

Example:

```markdown
Update the Sony Projector integration to expose [feature].

Context:

- Protocol/library support: [method, field, command, or missing upstream work]
- Expected HA surface: [media_player, sensor, service action, etc.]
- Existing files likely involved: [paths]

Requirements:

1. Keep protocol-library changes out of this repository.
2. Preserve Sony protocol state names exactly.
3. Follow Entities -> Coordinator -> API Client.
4. Run the project validation scripts.
```

## Testing Copilot Changes

After Copilot creates a draft pull request:

1. Open the PR branch in Codespaces.
2. Start Home Assistant with `./script/develop`.
3. Add or reload the Sony Projector integration from the UI.
4. Test against an actual projector where possible.
5. Check `config/home-assistant.log` for `custom_components.sony_projector` messages.

Copilot runs in GitHub Actions, so it cannot perform live Home Assistant UI testing with your projector.

## Tips

- Keep requests scoped to one feature or bug.
- Include exact protocol state names and raw values when debugging power state behavior.
- If a fix belongs in `sony_projector_protocol`, do that upstream first and then update the dependency here.
- Use `@copilot` in PR comments to iterate on review feedback.

## Resources

- [GitHub Copilot Coding Agent best practices](https://docs.github.com/en/copilot/tutorials/coding-agent/get-the-best-results)
- [AGENTS.md](../../AGENTS.md)
- [.github/copilot-instructions.md](../../.github/copilot-instructions.md)
