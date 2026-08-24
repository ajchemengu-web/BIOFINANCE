import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/routing_policy.dart';

/// Mock routing policy for Phase 1. Wired to GET/PUT /routing-policy in
/// Phase 2; the BioRouter algorithm that consumes this lands in Phase 3.
class RoutingPolicyNotifier extends StateNotifier<RoutingPolicy> {
  RoutingPolicyNotifier()
      : super(const RoutingPolicy(mode: RoutingMode.primary, primaryProviderCode: 'MPESA'));

  void update({RoutingMode? mode, String? primaryProviderCode, String? fallbackProviderCode}) {
    state = state.copyWith(
      mode: mode,
      primaryProviderCode: primaryProviderCode,
      fallbackProviderCode: fallbackProviderCode,
    );
  }
}

final routingPolicyProvider =
    StateNotifierProvider<RoutingPolicyNotifier, RoutingPolicy>((ref) => RoutingPolicyNotifier());
