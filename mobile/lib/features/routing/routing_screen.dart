import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/provider_connection.dart';
import '../../models/routing_policy.dart';
import '../providers/provider_connections_providers.dart';
import 'routing_policy_providers.dart';

/// Mirrors PRD §22 routing preferences, backed by real GET/PUT
/// /routing-policy (Phase 2). BioRouter itself reads this policy
/// server-side (Phase 3, backend/app/services/router_service.py).
class RoutingScreen extends ConsumerWidget {
  const RoutingScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final policyAsync = ref.watch(routingPolicyProvider);
    final connectionsAsync = ref.watch(providerConnectionsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Routing Policy')),
      body: policyAsync.when(
        data: (policy) => connectionsAsync.when(
          data: (connections) => _RoutingForm(
            policy: policy,
            connectedProviders: connections.where((c) => c.connected).toList(),
          ),
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => Center(child: Text('$error')),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(child: Text('$error')),
      ),
    );
  }
}

class _RoutingForm extends ConsumerWidget {
  const _RoutingForm({required this.policy, required this.connectedProviders});

  final RoutingPolicy policy;
  final List<ProviderConnection> connectedProviders;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifier = ref.read(routingPolicyProvider.notifier);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Mode', style: Theme.of(context).textTheme.titleMedium),
        RadioGroup<RoutingMode>(
          groupValue: policy.mode,
          onChanged: (value) {
            if (value != null) {
              notifier.updatePolicy(
                RoutingPolicy(
                  mode: value,
                  primaryProviderId: policy.primaryProviderId,
                  fallbackProviderId: policy.fallbackProviderId,
                ),
              );
            }
          },
          child: Column(
            children: [
              for (final mode in RoutingMode.values)
                RadioListTile<RoutingMode>(title: Text(mode.name.toUpperCase()), value: mode),
            ],
          ),
        ),
        const Divider(height: 32),
        Text('Preferred provider', style: Theme.of(context).textTheme.titleMedium),
        _ProviderDropdown(
          value: policy.primaryProviderId,
          options: connectedProviders,
          onChanged: (id) => notifier.updatePolicy(
            RoutingPolicy(mode: policy.mode, primaryProviderId: id, fallbackProviderId: policy.fallbackProviderId),
          ),
        ),
        const SizedBox(height: 16),
        Text('Fallback provider', style: Theme.of(context).textTheme.titleMedium),
        _ProviderDropdown(
          value: policy.fallbackProviderId,
          options: connectedProviders,
          allowNone: true,
          onChanged: (id) => notifier.updatePolicy(
            RoutingPolicy(mode: policy.mode, primaryProviderId: policy.primaryProviderId, fallbackProviderId: id),
          ),
        ),
      ],
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
  final List<ProviderConnection> options;
  final bool allowNone;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) {
    // A previously selected id that's no longer in the connected list (e.g.
    // disconnected since) would crash DropdownButtonFormField's assertion —
    // fall back to null rather than pass a dangling value.
    final validValue = options.any((o) => o.id == value) ? value : null;

    return DropdownButtonFormField<String?>(
      initialValue: validValue,
      decoration: const InputDecoration(border: OutlineInputBorder()),
      items: [
        if (allowNone) const DropdownMenuItem(value: null, child: Text('None')),
        for (final option in options)
          DropdownMenuItem(value: option.id, child: Text(providerDisplayName(option.providerCode))),
      ],
      onChanged: onChanged,
    );
  }
}
