import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/provider_catalog_entry.dart';
import '../../models/provider_connection.dart';
import 'provider_connections_providers.dart';

/// Mirrors PRD §21 "MY PROVIDERS" UI, backed by real GET/POST/DELETE
/// /providers (Phase 2) and the provider catalog (GET /provider-catalog,
/// docs/architecture.md "Provider catalog") instead of a hardcoded list —
/// this is the screen a new market/partner shows up on without a client
/// release: add a catalog row on the backend, it appears here.
class ProvidersScreen extends ConsumerWidget {
  const ProvidersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final catalogAsync = ref.watch(providerCatalogProvider);
    final connectionsAsync = ref.watch(providerConnectionsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('My Providers')),
      body: catalogAsync.when(
        data: (catalog) => connectionsAsync.when(
          data: (connections) => _ProviderList(catalog: catalog, connections: connections),
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => Center(child: Text('$error')),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(child: Text('$error')),
      ),
    );
  }
}

class _ProviderList extends ConsumerWidget {
  const _ProviderList({required this.catalog, required this.connections});

  final List<ProviderCatalogEntry> catalog;
  final List<ProviderConnection> connections;

  ProviderConnection? _connectedFor(String code) {
    for (final c in connections) {
      if (c.providerCode == code && c.connected) return c;
    }
    return null;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (catalog.isEmpty) {
      return const Center(child: Text('No providers available yet.'));
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        for (final entry in catalog)
          _ProviderTile(entry: entry, connection: _connectedFor(entry.code)),
      ],
    );
  }
}

class _ProviderTile extends ConsumerStatefulWidget {
  const _ProviderTile({required this.entry, required this.connection});

  final ProviderCatalogEntry entry;
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
        await notifier.connect(widget.entry.code);
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final connected = widget.connection != null;
    final available = widget.entry.isAvailable;
    return Card(
      child: ListTile(
        leading: Icon(
          connected ? Icons.check_circle : Icons.radio_button_unchecked,
          color: connected ? Colors.green : null,
        ),
        title: Text(widget.entry.displayName),
        subtitle: Text('${widget.entry.countryCode} · ${widget.entry.currency}'),
        trailing: !available
            ? Chip(label: Text(widget.entry.status.replaceAll('_', ' ')))
            : _busy
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : OutlinedButton(
                    onPressed: _toggle,
                    child: Text(connected ? 'Disconnect' : 'Connect'),
                  ),
      ),
    );
  }
}
