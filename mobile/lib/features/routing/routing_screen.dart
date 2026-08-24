import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/routing_policy.dart';
import '../providers/provider_connections_providers.dart';
import 'routing_policy_providers.dart';

/// Mirrors PRD §22 routing preferences. Mock/local until Phase 2 wires
/// PUT /routing-policy; BioRouter itself (which reads this policy to select
/// a provider) lands in Phase 3.
class RoutingScreen extends ConsumerWidget {
  const RoutingScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final policy = ref.watch(routingPolicyProvider);
    final connectedProviders =
        ref.watch(providerConnectionsProvider).where((c) => c.connected).toList();
    final notifier = ref.read(routingPolicyProvider.notifier);

    return Scaffold(
      appBar: AppBar(title: const Text('Routing Policy')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Mode', style: Theme.of(context).textTheme.titleMedium),
          RadioGroup<RoutingMode>(
            groupValue: policy.mode,
            onChanged: (value) {
              if (value != null) notifier.update(mode: value);
            },
            child: Column(
              children: [
                for (final mode in RoutingMode.values)
                  RadioListTile<RoutingMode>(
                    title: Text(mode.name.toUpperCase()),
                    value: mode,
                  ),
              ],
            ),
          ),
          const Divider(height: 32),
          Text('Preferred provider', style: Theme.of(context).textTheme.titleMedium),
          _ProviderDropdown(
            value: policy.primaryProviderCode,
            options: connectedProviders,
            onChanged: (code) => notifier.update(primaryProviderCode: code),
          ),
          const SizedBox(height: 16),
          Text('Fallback provider', style: Theme.of(context).textTheme.titleMedium),
          _ProviderDropdown(
            value: policy.fallbackProviderCode,
            options: connectedProviders,
            allowNone: true,
            onChanged: (code) => notifier.update(fallbackProviderCode: code),
          ),
        ],
      ),
    );
  }
}

class _ProviderDropdown extends StatelessWidget {
  const _ProviderDropdown({
    required this.value,
    required this.options,
    required this.onChanged,
    this.allowNone = false,
  });

  final String? value;
  final List<dynamic> options;
  final bool allowNone;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<String?>(
      initialValue: value,
      decoration: const InputDecoration(border: OutlineInputBorder()),
      items: [
        if (allowNone) const DropdownMenuItem(value: null, child: Text('None')),
        for (final option in options)
          DropdownMenuItem(value: option.providerCode as String, child: Text(option.displayName as String)),
      ],
      onChanged: onChanged,
    );
  }
}
