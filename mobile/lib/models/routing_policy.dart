enum RoutingMode { primary, priority, automatic, manual }

class RoutingPolicy {
  const RoutingPolicy({
    required this.mode,
    this.primaryProviderCode,
    this.fallbackProviderCode,
  });

  final RoutingMode mode;
  final String? primaryProviderCode;
  final String? fallbackProviderCode;

  RoutingPolicy copyWith({
    RoutingMode? mode,
    String? primaryProviderCode,
    String? fallbackProviderCode,
  }) =>
      RoutingPolicy(
        mode: mode ?? this.mode,
        primaryProviderCode: primaryProviderCode ?? this.primaryProviderCode,
        fallbackProviderCode: fallbackProviderCode ?? this.fallbackProviderCode,
      );
}
