import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/provider_balance.dart';
import '../providers/provider_connections_providers.dart';

const _seedAmounts = {'MPESA': 8500.0, 'EQUITY': 14200.0, 'AIRTEL': 2150.0};

/// Raw per-provider balances, mutated by the mock payment flow
/// (features/payments) so a decline-then-fallback demo (PRD §43) is
/// visible without a backend. Real balances come from GET /balances in
/// Phase 2.
class RawBalancesNotifier extends StateNotifier<Map<String, double>> {
  RawBalancesNotifier() : super(Map.of(_seedAmounts));

  bool debit(String providerCode, double amount) {
    final current = state[providerCode] ?? 0;
    if (current < amount) return false;
    state = {...state, providerCode: current - amount};
    return true;
  }
}

final rawBalancesProvider =
    StateNotifierProvider<RawBalancesNotifier, Map<String, double>>((ref) => RawBalancesNotifier());

/// Derives BioWallet balances from whichever providers are connected.
final balanceProvider = Provider<List<ProviderBalance>>((ref) {
  final connections = ref.watch(providerConnectionsProvider);
  final rawBalances = ref.watch(rawBalancesProvider);
  return [
    for (final connection in connections)
      if (connection.connected)
        ProviderBalance(
          providerCode: connection.providerCode,
          displayName: connection.displayName,
          amount: rawBalances[connection.providerCode] ?? 0,
        ),
  ];
});

final totalBalanceProvider = Provider<double>((ref) {
  final balances = ref.watch(balanceProvider);
  return balances.fold<double>(0, (sum, balance) => sum + balance.amount);
});
