import 'package:flutter_riverpod/flutter_riverpod.dart';

/// In-flight payment state (biometric auth → BioRouter → provider → result).
final paymentProvider = StateProvider<Object?>((ref) => null);
