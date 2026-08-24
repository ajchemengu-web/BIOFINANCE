import 'package:flutter_riverpod/flutter_riverpod.dart';

/// The user's BioRouter routing policy (mode, primary/fallback provider).
final routingPolicyProvider = StateProvider<Object?>((ref) => null);
