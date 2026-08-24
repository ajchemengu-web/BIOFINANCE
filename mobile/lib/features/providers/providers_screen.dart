import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/provider_connection.dart';
import 'provider_connections_providers.dart';

const _availableProviderCodes = ['MPESA', 'EQUITY', 'AIRTEL'];

/// Mirrors PRD §21 "MY PROVIDERS" UI, backed by real GET/POST/DELETE
/// /providers (Phase 2).
class ProvidersScreen extends ConsumerWidget {
  const ProvidersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final connectionsAsync = ref.watch(providerConnectionsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('My Providers')),
      body: connectionsAsync.when(
        data: (connections) => _ProviderList(connections: connections),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(child: Text('$error')),
      ),
    );
  }
}

class _ProviderList extends ConsumerWidget {
  const _ProviderList({required this.connections});

  final List<ProviderConnection> connections;

  ProviderConnection? _connectedFor(String code) {
    for (final c in connections) {
      if (c.providerCode == code && c.connected) return c;
    }
    return null;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        for (final code in _availableProviderCodes)
          _ProviderTile(code: code, connection: _connectedFor(code)),
      ],
    );
  }
}

class _ProviderTile extends ConsumerStatefulWidget {
  const _ProviderTile({required this.code, required this.connection});

  final String code;
  final ProviderConnection? connection;

  @override
  ConsumerState<_ProviderTile> createState() => _ProviderTileState();
}

class _ProviderTileState extends ConsumerState<_ProviderTile> {
  bool _busy = false;

  Future<void> _toggle() async {
    setState(() => _busy = true);
    final notifier = ref.read(providerConnectionsProvider.notifier);
    try {
      if (widget.connection != null) {
        await notifier.disconnect(widget.connection!.id);
      } else {
        await notifier.connect(widget.code);
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final connected = widget.connection != null;
    return Card(
      child: ListTile(
        leading: Icon(
          connected ? Icons.check_circle : Icons.radio_button_unchecked,
          color: connected ? Colors.green : null,
        ),
        title: Text(providerDisplayName(widget.code)),
        trailing: _busy
            ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
            : OutlinedButton(
                onPressed: _toggle,
                child: Text(connected ? 'Disconnect' : 'Connect'),
              ),
      ),
    );
  }
}
