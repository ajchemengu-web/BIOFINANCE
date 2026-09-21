import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/provider_catalog_entry.dart';
import '../../models/provider_connection.dart';
import '../../repositories/provider_catalog_repository.dart';
import '../../repositories/providers_repository.dart';
import '../authentication/auth_providers.dart';
import '../bioid/bioid_providers.dart';

/// The selectable provider list (docs/architecture.md "Provider catalog") —
/// fetched from the backend instead of hardcoded, so a new market/partner
/// shows up here without a client release. Reference data, not tied to the
/// user session.
final providerCatalogProvider = FutureProvider<List<ProviderCatalogEntry>>(
  (ref) => ref.watch(providerCatalogRepositoryProvider).list(),
);

/// Connected providers, backed by GET/POST/DELETE /providers (Phase 2).
class ProviderConnectionsNotifier extends AsyncNotifier<List<ProviderConnection>> {
  @override
  Future<List<ProviderConnection>> build() {
    ref.watch(authProvider.select((s) => s.isAuthenticated));
    return ref.watch(providersRepositoryProvider).list();
  }

  Future<void> connect(String providerCode) async {
    // Keyed by the user's own BioID, not a shared constant — the mock
    // providers (backend/app/providers/registry.py) key balances by this
    // account ref, so two different users connecting the same provider
    // must not land on the same mock account or they'd see (and spend)
    // each other's balance.
    final bioId = await ref.read(bioIdProvider.future);
    final accountRef = '$providerCode-${bioId.code}';
    await ref.read(providersRepositoryProvider).connect(providerCode, accountRef);
    ref.invalidateSelf();
    await future;
  }

  Future<void> disconnect(String connectionId) async {
    await ref.read(providersRepositoryProvider).disconnect(connectionId);
    ref.invalidateSelf();
    await future;
  }
}

final providerConnectionsProvider =
    AsyncNotifierProvider<ProviderConnectionsNotifier, List<ProviderConnection>>(
  ProviderConnectionsNotifier.new,
);
