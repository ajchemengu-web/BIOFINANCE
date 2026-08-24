import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/provider_connection.dart';

const _seedConnections = [
  ProviderConnection(providerCode: 'MPESA', displayName: 'M-PESA', connected: true),
  ProviderConnection(providerCode: 'EQUITY', displayName: 'Equity', connected: false),
  ProviderConnection(providerCode: 'AIRTEL', displayName: 'Airtel Money', connected: false),
];

/// Mock provider connections for Phase 1. Wired to GET/POST /providers in
/// Phase 2 (docs/roadmap.md) — the backend equivalent already exists as
/// stubs in app/api/providers.py.
class ProviderConnectionsNotifier extends StateNotifier<List<ProviderConnection>> {
  ProviderConnectionsNotifier() : super(_seedConnections);

  void toggle(String providerCode) {
    state = [
      for (final connection in state)
        if (connection.providerCode == providerCode)
          connection.copyWith(connected: !connection.connected)
        else
          connection,
    ];
  }
}

final providerConnectionsProvider =
    StateNotifierProvider<ProviderConnectionsNotifier, List<ProviderConnection>>(
  (ref) => ProviderConnectionsNotifier(),
);
