# Homebrew formula for skilldrop-cli. Lives in the tap repository (sananthanarayan/homebrew-skilldrop)
# as Formula/skilldrop.rb; this copy is the source. Bump with packaging/homebrew/update_formula.py.
class Skilldrop < Formula
  desc "Portable AI-agent skills for Claude Code, Cursor, Kiro, Codex, Copilot and more"
  homepage "https://sananthanarayan.github.io/skilldrop/"
  url "https://registry.npmjs.org/skilldrop-cli/-/skilldrop-cli-0.13.7.tgz"
  sha256 "ad474eeb57380055877037e514b75d7cab121dd08ff59a3133441bb916eb8b39"
  license "MIT"

  depends_on "node"

  def install
    system "npm", "install", *std_npm_args
    bin.install_symlink Dir["#{libexec}/bin/*"]
  end

  test do
    assert_match "doc-critique", shell_output("#{bin}/skilldrop list")
  end
end
