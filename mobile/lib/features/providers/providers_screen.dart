import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'provider_connections_providers.dart';

/// Mirrors PRD §21 "MY PROVIDERS" UI. Connect/disconnect is local-only
/// (mock) until Phase 2 wires POST /providers/connect.
class ProvidersScreen extends ConsumerWidget {
  const ProvidersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final connections = ref.watch(providerConnectionsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('My Providers')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          for (final connection in connections)
            Card(
              child: ListTile(
                leading: Icon(
                  connection.connected ? Icons.check_circle : Icons.radio_button_unchecked,
                  color: connection.connected ? Colors.green : null,
                ),
                title: Text(connection.displayName),
                trailing: OutlinedButton(
                  onPressed: () =>
                      ref.read(providerConnectionsProvider.notifier).toggle(connection.providerCode),
                  child: Text(connection.connected ? 'Disconnect' : 'Connect'),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
