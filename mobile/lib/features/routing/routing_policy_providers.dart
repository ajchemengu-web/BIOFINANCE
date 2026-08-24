import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/routing_policy.dart';
import '../../repositories/routing_repository.dart';
import '../authentication/auth_providers.dart';

/// Routing policy (GET/PUT /routing-policy, Phase 2). BioRouter itself
/// (which reads this policy server-side to pick a provider) lives in
/// backend/app/services/router_service.py.
class RoutingPolicyNotifier extends AsyncNotifier<RoutingPolicy> {
  @override
  Future<RoutingPolicy> build() {
    ref.watch(authProvider.select((s) => s.isAuthenticated));
    return ref.watch(routingRepositoryProvider).fetch();
  }

  /// Takes the full desired policy rather than a partial patch — RoutingPolicy
  /// fields are nullable, so a `copyWith(fallbackProviderId: null)` can't
  /// distinguish "leave unchanged" from "clear it"; the caller always has the
  /// complete current+edited state in hand anyway (see routing_screen.dart).
  Future<void> updatePolicy(RoutingPolicy policy) async {
    state = const AsyncLoading<RoutingPolicy>().copyWithPrevious(state);
    state = await AsyncValue.guard(() => ref.read(routingRepositoryProvider).update(policy));
  }
}

final routingPolicyProvider =
    AsyncNotifierProvider<RoutingPolicyNotifier, RoutingPolicy>(RoutingPolicyNotifier.new);
